"""Oracle database connector using oracledb (thin mode)."""

import asyncio
from typing import Any

import pandas as pd

from biai.db.base import DatabaseConnector
from biai.models.connection import ConnectionConfig, DBType
from biai.models.schema import TableInfo, ColumnInfo, SchemaSnapshot
from biai.utils.logger import get_logger

logger = get_logger(__name__)


class OracleConnector(DatabaseConnector):
    """Oracle database connector using python-oracledb thin mode."""

    def __init__(self, config: ConnectionConfig):
        assert config.db_type == DBType.ORACLE
        super().__init__(config)
        self._pool: Any = None

    async def connect(self) -> None:
        import oracledb

        dsn = self.config.get_oracle_dsn()
        logger.info("connecting_oracle", dsn=dsn)

        self._pool = await asyncio.to_thread(
            oracledb.create_pool,
            user=self.config.username,
            password=self.config.password,
            dsn=dsn,
            min=1,
            max=4,
        )
        self._connection = True  # Flag to indicate connected state
        logger.info("oracle_connected")

    async def disconnect(self) -> None:
        if self._pool:
            await asyncio.to_thread(self._pool.close, force=True)
            self._pool = None
        self._connection = None
        logger.info("oracle_disconnected")

    async def test_connection(self) -> tuple[bool, str]:
        try:
            import oracledb

            dsn = self.config.get_oracle_dsn()
            conn = await asyncio.to_thread(
                oracledb.connect,
                user=self.config.username,
                password=self.config.password,
                dsn=dsn,
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            cursor.close()
            version = conn.version
            conn.close()
            return True, f"Oracle {version}"
        except Exception as e:
            return False, str(e)

    async def execute_query(self, sql: str, timeout: int = 30) -> pd.DataFrame:
        if not self._pool:
            raise RuntimeError("Not connected to Oracle")

        def _exec():
            conn = self._pool.acquire()
            try:
                cursor = conn.cursor()
                cursor.execute(sql)
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                cursor.close()
                return pd.DataFrame(rows, columns=columns)
            finally:
                self._pool.release(conn)

        return await asyncio.wait_for(
            asyncio.to_thread(_exec),
            timeout=timeout,
        )

    async def get_tables(self, schema: str = "") -> list[TableInfo]:
        """Get tables with columns, PKs, and FKs using batch queries.

        Uses 3 batch queries instead of N+1 per-table queries:
        1. All columns in one query
        2. All PKs in one query
        3. All FKs in one query (with cross-schema reference support)
        """
        if not self._pool:
            raise RuntimeError("Not connected to Oracle")

        schema_filter = schema.upper() if schema else "USER"

        def _get():
            conn = self._pool.acquire()
            try:
                cursor = conn.cursor()

                # Resolve actual owner
                if schema_filter == "USER":
                    cursor.execute("SELECT USER FROM DUAL")
                    actual_owner = cursor.fetchone()[0]
                else:
                    actual_owner = schema_filter

                # Get table names (including views)
                if schema_filter == "USER":
                    cursor.execute("""
                        SELECT table_name, 'TABLE' AS object_type FROM user_tables
                        UNION ALL
                        SELECT view_name, 'VIEW' AS object_type FROM user_views
                        ORDER BY 1
                    """)
                else:
                    cursor.execute("""
                        SELECT table_name, 'TABLE' AS object_type FROM all_tables WHERE owner = :owner
                        UNION ALL
                        SELECT view_name, 'VIEW' AS object_type FROM all_views WHERE owner = :owner
                        ORDER BY 1
                    """, owner=actual_owner)
                name_rows = cursor.fetchall()
                table_names = [row[0] for row in name_rows]
                object_types = {row[0]: row[1] for row in name_rows}

                if not table_names:
                    cursor.close()
                    return []

                # --- BATCH 1: All columns in one query ---
                cursor.execute("""
                    SELECT table_name, column_name, data_type, nullable, data_length
                    FROM all_tab_columns
                    WHERE owner = :owner
                    ORDER BY table_name, column_id
                """, owner=actual_owner)
                all_cols_rows = cursor.fetchall()

                # Group by table
                from collections import defaultdict
                cols_by_table: dict[str, list] = defaultdict(list)
                for row in all_cols_rows:
                    cols_by_table[row[0]].append(row[1:])  # (col_name, dtype, nullable, length)

                # --- BATCH 2: All PKs in one query ---
                cursor.execute("""
                    SELECT cons.table_name, cols.column_name
                    FROM all_constraints cons
                    JOIN all_cons_columns cols
                      ON cons.owner = cols.owner
                      AND cons.constraint_name = cols.constraint_name
                    WHERE cons.constraint_type = 'P'
                      AND cons.owner = :owner
                """, owner=actual_owner)
                pk_by_table: dict[str, set[str]] = defaultdict(set)
                for row in cursor.fetchall():
                    pk_by_table[row[0]].add(row[1])

                # --- BATCH 3: All FKs in one query (with cross-schema ref) ---
                cursor.execute("""
                    SELECT cons.table_name, cols.column_name,
                           r_cons.owner AS ref_schema,
                           r_cons.table_name AS ref_table
                    FROM all_constraints cons
                    JOIN all_cons_columns cols
                      ON cons.owner = cols.owner
                      AND cons.constraint_name = cols.constraint_name
                    JOIN all_constraints r_cons
                      ON cons.r_constraint_name = r_cons.constraint_name
                      AND cons.r_owner = r_cons.owner
                    WHERE cons.constraint_type = 'R'
                      AND cons.owner = :owner
                """, owner=actual_owner)
                # fk_by_table[table_name] = {col_name: "REF_SCHEMA.REF_TABLE" or "REF_TABLE"}
                fk_by_table: dict[str, dict[str, str]] = defaultdict(dict)
                for row in cursor.fetchall():
                    tname, col_name, ref_schema, ref_table = row
                    # Include schema prefix for cross-schema FKs
                    if ref_schema and ref_schema != actual_owner:
                        fk_by_table[tname][col_name] = f"{ref_schema}.{ref_table}"
                    else:
                        fk_by_table[tname][col_name] = ref_table

                cursor.close()

                # --- Assemble TableInfo objects ---
                tables = []
                for tname in table_names:
                    col_rows = cols_by_table.get(tname, [])
                    pk_columns = pk_by_table.get(tname, set())
                    fk_map = fk_by_table.get(tname, {})

                    columns = []
                    for col_row in col_rows:
                        col_name, dtype, nullable, length = col_row
                        columns.append(ColumnInfo(
                            name=col_name,
                            data_type=f"{dtype}({length})" if length else dtype,
                            nullable=nullable == "Y",
                            is_primary_key=col_name in pk_columns,
                            is_foreign_key=col_name in fk_map,
                            foreign_key_ref=fk_map.get(col_name),
                        ))

                    tables.append(TableInfo(
                        name=tname,
                        schema_name=schema_filter if schema_filter != "USER" else "",
                        columns=columns,
                        object_type=object_types.get(tname, "TABLE"),
                    ))

                return tables
            finally:
                self._pool.release(conn)

        return await asyncio.to_thread(_get)

    async def get_schema_snapshot(self, schema: str = "") -> SchemaSnapshot:
        tables = await self.get_tables(schema)
        triggers = await self.get_triggers(schema)
        procedures = await self.get_procedures(schema)
        dependencies = await self.get_dependencies(schema)
        return SchemaSnapshot(
            tables=tables,
            triggers=triggers,
            procedures=procedures,
            dependencies=dependencies,
            db_type="oracle",
            schema_name=schema or "USER",
        )

    async def get_triggers(self, schema: str = "") -> list:
        """Discover triggers — reveals business logic transitions."""
        if not self._pool:
            return []
        from biai.models.schema import TriggerInfo
        schema_filter = schema.upper() if schema else "USER"

        def _get():
            conn = self._pool.acquire()
            try:
                cursor = conn.cursor()
                if schema_filter == "USER":
                    cursor.execute("""
                        SELECT trigger_name, table_name,
                               triggering_event, trigger_type,
                               DBMS_METADATA.GET_DDL('TRIGGER', trigger_name)
                        FROM user_triggers
                        WHERE table_name IS NOT NULL
                    """)
                    owner = ""
                else:
                    cursor.execute("""
                        SELECT trigger_name, table_name,
                               triggering_event, trigger_type, ''
                        FROM all_triggers
                        WHERE owner = :owner AND table_name IS NOT NULL
                    """, owner=schema_filter)
                    owner = schema_filter
                results = []
                for row in cursor.fetchall():
                    # Truncate trigger body to 500 chars
                    body = str(row[4] or "")[:500]
                    timing = ""
                    ttype = str(row[3] or "")
                    if "BEFORE" in ttype:
                        timing = "BEFORE"
                    elif "AFTER" in ttype:
                        timing = "AFTER"
                    elif "INSTEAD" in ttype:
                        timing = "INSTEAD OF"
                    results.append(TriggerInfo(
                        trigger_name=row[0],
                        table_name=row[1],
                        trigger_event=str(row[2] or ""),
                        timing=timing,
                        trigger_body=body,
                        schema_name=owner,
                    ))
                cursor.close()
                return results
            except Exception:
                return []
            finally:
                self._pool.release(conn)

        return await asyncio.to_thread(_get)

    async def get_procedures(self, schema: str = "") -> list:
        """Discover stored procedures/packages."""
        if not self._pool:
            return []
        from biai.models.schema import ProcedureInfo
        schema_filter = schema.upper() if schema else "USER"

        def _get():
            conn = self._pool.acquire()
            try:
                cursor = conn.cursor()
                if schema_filter == "USER":
                    cursor.execute("""
                        SELECT object_name, object_type, procedure_name
                        FROM user_procedures
                        WHERE object_type IN ('PROCEDURE', 'FUNCTION', 'PACKAGE')
                        ORDER BY object_name
                    """)
                    owner = ""
                else:
                    cursor.execute("""
                        SELECT object_name, object_type, procedure_name
                        FROM all_procedures
                        WHERE owner = :owner
                          AND object_type IN ('PROCEDURE', 'FUNCTION', 'PACKAGE')
                        ORDER BY object_name
                    """, owner=schema_filter)
                    owner = schema_filter
                results = []
                for row in cursor.fetchall():
                    results.append(ProcedureInfo(
                        name=row[0],
                        object_type=row[1] or "PROCEDURE",
                        schema_name=owner,
                        sub_program=row[2] or "",
                    ))
                cursor.close()
                return results
            except Exception:
                return []
            finally:
                self._pool.release(conn)

        return await asyncio.to_thread(_get)

    async def get_dependencies(self, schema: str = "") -> list:
        """Discover object dependencies (which procs use which tables)."""
        if not self._pool:
            return []
        from biai.models.schema import DependencyInfo
        schema_filter = schema.upper() if schema else "USER"

        def _get():
            conn = self._pool.acquire()
            try:
                cursor = conn.cursor()
                if schema_filter == "USER":
                    cursor.execute("""
                        SELECT name, type, referenced_name, referenced_type
                        FROM user_dependencies
                        WHERE referenced_type IN ('TABLE', 'VIEW')
                          AND type IN ('PROCEDURE', 'FUNCTION', 'TRIGGER', 'PACKAGE BODY')
                        ORDER BY name
                    """)
                    owner = ""
                else:
                    cursor.execute("""
                        SELECT name, type, referenced_name, referenced_type
                        FROM all_dependencies
                        WHERE owner = :owner
                          AND referenced_type IN ('TABLE', 'VIEW')
                          AND type IN ('PROCEDURE', 'FUNCTION', 'TRIGGER', 'PACKAGE BODY')
                        ORDER BY name
                    """, owner=schema_filter)
                    owner = schema_filter
                results = []
                for row in cursor.fetchall():
                    results.append(DependencyInfo(
                        name=row[0],
                        object_type=row[1] or "",
                        referenced_name=row[2] or "",
                        referenced_type=row[3] or "",
                        schema_name=owner,
                    ))
                cursor.close()
                return results
            except Exception:
                return []
            finally:
                self._pool.release(conn)

        return await asyncio.to_thread(_get)

    async def get_schemas(self) -> list[str]:
        if not self._pool:
            raise RuntimeError("Not connected to Oracle")

        sql = """
            SELECT username FROM all_users
            WHERE username NOT IN (
                'SYS','SYSTEM','OUTLN','DBSNMP','XDB',
                'CTXSYS','MDSYS','ORDDATA','OLAPSYS','WMSYS','GSMADMIN_INTERNAL',
                'APPQOSSYS','ANONYMOUS','LBACSYS','ORACLE_OCM','ORDSYS',
                'SI_INFORMTN_SCHEMA','DVSYS','DBSFWUSER','REMOTE_SCHEDULER_AGENT',
                'DIP','OJVMSYS','GGSYS','MDDATA','XS$NULL','FLOWS_FILES',
                'APEX_PUBLIC_USER','APEX_040000','APEX_040200','APEX_050000',
                'APEX_230100',
                'AUDSYS','DGPDB_INT','DVF','GSMCATUSER','GSMUSER',
                'PDBADMIN','SYSBACKUP','SYSDG','SYSKM','SYSRAC',
                'GGSHAREDCAP','GSMROOTUSER'
            )
            AND username NOT LIKE 'APEX%'
            AND username NOT LIKE 'FLOWS_%'
            AND username NOT LIKE 'OPS$%'
            AND username NOT LIKE 'SYS$%'
            ORDER BY username
        """
        df = await self.execute_query(sql)
        if df.empty:
            return []
        return df.iloc[:, 0].tolist()

    async def get_server_version(self) -> str:
        if not self._pool:
            return "Not connected"

        def _ver():
            conn = self._pool.acquire()
            try:
                return conn.version
            finally:
                self._pool.release(conn)

        return await asyncio.to_thread(_ver)

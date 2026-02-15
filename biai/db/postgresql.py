"""PostgreSQL database connector using asyncpg."""

import asyncio

import asyncpg
import pandas as pd

from biai.db.base import DatabaseConnector
from biai.models.connection import ConnectionConfig, DBType
from biai.models.schema import TableInfo, ColumnInfo, SchemaSnapshot
from biai.utils.logger import get_logger

logger = get_logger(__name__)


class PostgreSQLConnector(DatabaseConnector):
    """PostgreSQL database connector using asyncpg."""

    def __init__(self, config: ConnectionConfig):
        assert config.db_type == DBType.POSTGRESQL
        super().__init__(config)
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        dsn = self.config.get_postgresql_dsn()
        logger.info("connecting_postgresql", dsn=dsn[:30])

        self._pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=1,
            max_size=4,
        )
        self._connection = True
        logger.info("postgresql_connected")

    async def disconnect(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None
        self._connection = None
        logger.info("postgresql_disconnected")

    async def test_connection(self) -> tuple[bool, str]:
        try:
            dsn = self.config.get_postgresql_dsn()
            conn = await asyncpg.connect(dsn=dsn)
            version = await conn.fetchval("SELECT version()")
            await conn.close()
            return True, version or "PostgreSQL"
        except Exception as e:
            return False, str(e)

    async def execute_query(self, sql: str, timeout: int = 30) -> pd.DataFrame:
        if not self._pool:
            raise RuntimeError("Not connected to PostgreSQL")

        async with self._pool.acquire() as conn:
            rows = await asyncio.wait_for(
                conn.fetch(sql),
                timeout=timeout,
            )
            if not rows:
                return pd.DataFrame()
            columns = list(rows[0].keys())
            data = [list(row.values()) for row in rows]
            return pd.DataFrame(data, columns=columns)

    async def get_tables(self, schema: str = "public") -> list[TableInfo]:
        """Get tables with columns, PKs, and FKs using batch queries.

        Uses 3 batch queries instead of N+1 per-table queries:
        1. All columns in one query
        2. All PKs in one query
        3. All FKs in one query (with cross-schema reference support)
        """
        if not self._pool:
            raise RuntimeError("Not connected to PostgreSQL")

        # Default to "public" if empty string passed
        if not schema:
            schema = "public"

        async with self._pool.acquire() as conn:
            # Get table names (including views)
            table_rows = await conn.fetch("""
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = $1
                AND table_type IN ('BASE TABLE', 'VIEW')
                ORDER BY table_name
            """, schema)

            if not table_rows:
                return []

            table_names = [row["table_name"] for row in table_rows]
            table_types = {row["table_name"]: row["table_type"] for row in table_rows}

            # --- BATCH 1: All columns in one query ---
            col_rows = await conn.fetch("""
                SELECT table_name, column_name, data_type, is_nullable,
                       character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = $1
                ORDER BY table_name, ordinal_position
            """, schema)

            from collections import defaultdict
            cols_by_table: dict[str, list] = defaultdict(list)
            for row in col_rows:
                cols_by_table[row["table_name"]].append(row)

            # --- BATCH 2: All PKs in one query ---
            pk_rows = await conn.fetch("""
                SELECT tc.table_name, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                WHERE tc.table_schema = $1
                  AND tc.constraint_type = 'PRIMARY KEY'
            """, schema)

            pk_by_table: dict[str, set[str]] = defaultdict(set)
            for row in pk_rows:
                pk_by_table[row["table_name"]].add(row["column_name"])

            # --- BATCH 3: All FKs in one query (with cross-schema ref) ---
            fk_rows = await conn.fetch("""
                SELECT kcu.table_name, kcu.column_name,
                       ccu.table_schema AS ref_schema,
                       ccu.table_name AS ref_table
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                    ON tc.constraint_name = ccu.constraint_name
                    AND tc.table_schema = ccu.constraint_schema
                WHERE tc.table_schema = $1
                  AND tc.constraint_type = 'FOREIGN KEY'
            """, schema)

            # fk_by_table[table] = {col: "ref_schema.ref_table" or "ref_table"}
            fk_by_table: dict[str, dict[str, str]] = defaultdict(dict)
            for row in fk_rows:
                ref_schema = row["ref_schema"]
                ref_table = row["ref_table"]
                # Include schema prefix for cross-schema FKs
                if ref_schema and ref_schema != schema:
                    fk_by_table[row["table_name"]][row["column_name"]] = f"{ref_schema}.{ref_table}"
                else:
                    fk_by_table[row["table_name"]][row["column_name"]] = ref_table

            # --- Assemble TableInfo objects ---
            tables = []
            table_set = set(table_names)
            for tname in table_names:
                pk_columns = pk_by_table.get(tname, set())
                fk_map = fk_by_table.get(tname, {})

                columns = []
                for crow in cols_by_table.get(tname, []):
                    dtype = crow["data_type"]
                    max_len = crow["character_maximum_length"]
                    if max_len:
                        dtype = f"{dtype}({max_len})"

                    col_name = crow["column_name"]
                    columns.append(ColumnInfo(
                        name=col_name,
                        data_type=dtype,
                        nullable=crow["is_nullable"] == "YES",
                        is_primary_key=col_name in pk_columns,
                        is_foreign_key=col_name in fk_map,
                        foreign_key_ref=fk_map.get(col_name),
                    ))

                # Map information_schema table_type to our object_type
                raw_type = table_types.get(tname, "BASE TABLE")
                obj_type = "VIEW" if raw_type == "VIEW" else "TABLE"

                tables.append(TableInfo(
                    name=tname,
                    schema_name=schema,
                    columns=columns,
                    object_type=obj_type,
                ))

            return tables

    async def get_schema_snapshot(self, schema: str = "public") -> SchemaSnapshot:
        tables = await self.get_tables(schema)
        triggers = await self.get_triggers(schema)
        procedures = await self.get_procedures(schema)
        return SchemaSnapshot(
            tables=tables,
            triggers=triggers,
            procedures=procedures,
            db_type="postgresql",
            schema_name=schema,
        )

    async def get_triggers(self, schema: str = "public") -> list:
        """Discover triggers on tables."""
        if not self._pool:
            return []
        if not schema:
            schema = "public"
        from biai.models.schema import TriggerInfo
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT trigger_name, event_object_table,
                           event_manipulation, action_timing,
                           LEFT(action_statement, 500) AS body
                    FROM information_schema.triggers
                    WHERE trigger_schema = $1
                """, schema)
                return [
                    TriggerInfo(
                        trigger_name=row["trigger_name"],
                        table_name=row["event_object_table"],
                        trigger_event=row["event_manipulation"] or "",
                        timing=row["action_timing"] or "",
                        trigger_body=row["body"] or "",
                        schema_name=schema,
                    )
                    for row in rows
                ]
        except Exception:
            return []

    async def get_procedures(self, schema: str = "public") -> list:
        """Discover functions and procedures."""
        if not self._pool:
            return []
        if not schema:
            schema = "public"
        from biai.models.schema import ProcedureInfo
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT routine_name, routine_type
                    FROM information_schema.routines
                    WHERE routine_schema = $1
                    ORDER BY routine_name
                """, schema)
                return [
                    ProcedureInfo(
                        name=row["routine_name"],
                        object_type=row["routine_type"] or "FUNCTION",
                        schema_name=schema,
                    )
                    for row in rows
                ]
        except Exception:
            return []

    async def get_schemas(self) -> list[str]:
        if not self._pool:
            raise RuntimeError("Not connected to PostgreSQL")

        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT schema_name FROM information_schema.schemata
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                AND schema_name NOT LIKE 'pg_temp_%'
                AND schema_name NOT LIKE 'pg_toast_temp_%'
                ORDER BY schema_name
            """)
            return [row["schema_name"] for row in rows]

    async def get_server_version(self) -> str:
        if not self._pool:
            return "Not connected"
        async with self._pool.acquire() as conn:
            return await conn.fetchval("SELECT version()")

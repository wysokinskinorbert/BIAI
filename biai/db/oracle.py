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
        if not self._pool:
            raise RuntimeError("Not connected to Oracle")

        schema_filter = schema.upper() if schema else "USER"

        def _get():
            conn = self._pool.acquire()
            try:
                cursor = conn.cursor()

                # Get tables
                if schema_filter == "USER":
                    cursor.execute(
                        "SELECT table_name FROM user_tables ORDER BY table_name"
                    )
                else:
                    cursor.execute(
                        "SELECT table_name FROM all_tables WHERE owner = :owner ORDER BY table_name",
                        owner=schema_filter,
                    )
                table_names = [row[0] for row in cursor.fetchall()]

                tables = []
                for tname in table_names:
                    # Get columns
                    owner_prefix = f"{schema_filter}." if schema_filter != "USER" else ""
                    cursor.execute(f"""
                        SELECT column_name, data_type, nullable, data_length
                        FROM all_tab_columns
                        WHERE table_name = :tname
                        AND owner = NVL(:owner, USER)
                        ORDER BY column_id
                    """, tname=tname, owner=schema_filter if schema_filter != "USER" else None)

                    columns = []
                    for col_row in cursor.fetchall():
                        columns.append(ColumnInfo(
                            name=col_row[0],
                            data_type=f"{col_row[1]}({col_row[3]})" if col_row[3] else col_row[1],
                            nullable=col_row[2] == "Y",
                        ))

                    tables.append(TableInfo(
                        name=tname,
                        schema_name=schema_filter if schema_filter != "USER" else "",
                        columns=columns,
                    ))

                cursor.close()
                return tables
            finally:
                self._pool.release(conn)

        return await asyncio.to_thread(_get)

    async def get_schema_snapshot(self, schema: str = "") -> SchemaSnapshot:
        tables = await self.get_tables(schema)
        return SchemaSnapshot(
            tables=tables,
            db_type="oracle",
            schema_name=schema or "USER",
        )

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

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
        if not self._pool:
            raise RuntimeError("Not connected to PostgreSQL")

        async with self._pool.acquire() as conn:
            # Get tables
            table_rows = await conn.fetch("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = $1
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, schema)

            tables = []
            for trow in table_rows:
                tname = trow["table_name"]

                # Get columns
                col_rows = await conn.fetch("""
                    SELECT
                        c.column_name,
                        c.data_type,
                        c.is_nullable,
                        c.character_maximum_length,
                        CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END AS is_pk,
                        CASE WHEN fk.column_name IS NOT NULL THEN true ELSE false END AS is_fk,
                        fk.foreign_table_name
                    FROM information_schema.columns c
                    LEFT JOIN (
                        SELECT kcu.column_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu
                            ON tc.constraint_name = kcu.constraint_name
                        WHERE tc.table_name = $1 AND tc.table_schema = $2
                        AND tc.constraint_type = 'PRIMARY KEY'
                    ) pk ON c.column_name = pk.column_name
                    LEFT JOIN (
                        SELECT
                            kcu.column_name,
                            ccu.table_name AS foreign_table_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu
                            ON tc.constraint_name = kcu.constraint_name
                        JOIN information_schema.constraint_column_usage ccu
                            ON tc.constraint_name = ccu.constraint_name
                        WHERE tc.table_name = $1 AND tc.table_schema = $2
                        AND tc.constraint_type = 'FOREIGN KEY'
                    ) fk ON c.column_name = fk.column_name
                    WHERE c.table_name = $1 AND c.table_schema = $2
                    ORDER BY c.ordinal_position
                """, tname, schema)

                columns = []
                for crow in col_rows:
                    dtype = crow["data_type"]
                    max_len = crow["character_maximum_length"]
                    if max_len:
                        dtype = f"{dtype}({max_len})"

                    columns.append(ColumnInfo(
                        name=crow["column_name"],
                        data_type=dtype,
                        nullable=crow["is_nullable"] == "YES",
                        is_primary_key=crow["is_pk"],
                        is_foreign_key=crow["is_fk"],
                        foreign_key_ref=crow["foreign_table_name"],
                    ))

                tables.append(TableInfo(
                    name=tname,
                    schema_name=schema,
                    columns=columns,
                ))

            return tables

    async def get_schema_snapshot(self, schema: str = "public") -> SchemaSnapshot:
        tables = await self.get_tables(schema)
        return SchemaSnapshot(
            tables=tables,
            db_type="postgresql",
            schema_name=schema,
        )

    async def get_server_version(self) -> str:
        if not self._pool:
            return "Not connected"
        async with self._pool.acquire() as conn:
            return await conn.fetchval("SELECT version()")

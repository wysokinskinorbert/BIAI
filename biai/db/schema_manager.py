"""Schema manager with caching."""

import time

from biai.db.base import DatabaseConnector
from biai.models.schema import SchemaSnapshot, TableInfo
from biai.config.constants import SCHEMA_CACHE_TTL
from biai.utils.logger import get_logger

logger = get_logger(__name__)


class SchemaManager:
    """Manages database schema with TTL-based caching."""

    def __init__(self, connector: DatabaseConnector, cache_ttl: int = SCHEMA_CACHE_TTL):
        self._connector = connector
        self._cache_ttl = cache_ttl
        self._cache: SchemaSnapshot | None = None
        self._cache_time: float = 0.0

    @property
    def is_cache_valid(self) -> bool:
        if self._cache is None:
            return False
        return (time.time() - self._cache_time) < self._cache_ttl

    async def get_snapshot(self, schema: str = "", force_refresh: bool = False) -> SchemaSnapshot:
        """Get schema snapshot (cached)."""
        if self.is_cache_valid and not force_refresh:
            logger.debug("schema_cache_hit")
            return self._cache  # type: ignore

        logger.info("schema_cache_miss", force_refresh=force_refresh)
        self._cache = await self._connector.get_schema_snapshot(schema)
        self._cache_time = time.time()
        return self._cache

    async def get_tables(self, schema: str = "", force_refresh: bool = False) -> list[TableInfo]:
        """Get table list (from cache)."""
        snapshot = await self.get_snapshot(schema, force_refresh)
        return snapshot.tables

    async def get_ddl_statements(self, schema: str = "") -> list[str]:
        """Generate DDL statements for all tables (for Vanna training)."""
        snapshot = await self.get_snapshot(schema)
        return [table.get_ddl() for table in snapshot.tables]

    async def get_table_names(self, schema: str = "") -> list[str]:
        """Get list of table names."""
        tables = await self.get_tables(schema)
        return [t.name for t in tables]

    async def get_unified_snapshot(self, schemas: list[str]) -> SchemaSnapshot:
        """Get a unified snapshot across multiple schemas.

        Tables are fully qualified with schema prefix (e.g. "sales.orders").
        FK refs also include schema prefix for cross-schema relationships.
        """
        if not schemas:
            return await self.get_snapshot()

        all_tables = []
        all_triggers = []
        all_procedures = []
        all_dependencies = []

        for schema in schemas:
            snapshot = await self._connector.get_schema_snapshot(schema)
            # Ensure all table names are schema-qualified
            for table in snapshot.tables:
                if not table.schema_name:
                    table.schema_name = schema
            all_tables.extend(snapshot.tables)
            all_triggers.extend(snapshot.triggers)
            all_procedures.extend(snapshot.procedures)
            all_dependencies.extend(snapshot.dependencies)

        return SchemaSnapshot(
            tables=all_tables,
            triggers=all_triggers,
            procedures=all_procedures,
            dependencies=all_dependencies,
            db_type=all_tables[0].schema_name if all_tables else "",
            schema_name=",".join(schemas),
        )

    def invalidate_cache(self) -> None:
        """Force cache invalidation."""
        self._cache = None
        self._cache_time = 0.0

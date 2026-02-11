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

    def invalidate_cache(self) -> None:
        """Force cache invalidation."""
        self._cache = None
        self._cache_time = 0.0

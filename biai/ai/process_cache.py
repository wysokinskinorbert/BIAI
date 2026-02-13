"""Cache for process discovery results."""

import time

from biai.models.connection import ConnectionConfig
from biai.models.discovery import DiscoveredProcess
from biai.config.constants import DISCOVERY_CACHE_TTL
from biai.utils.logger import get_logger

logger = get_logger(__name__)


def _cache_key(config: ConnectionConfig) -> str:
    """Build a cache key from connection config."""
    return f"{config.db_type.value}:{config.host}:{config.port}:{config.database}"


class ProcessDiscoveryCache:
    """TTL-based cache for discovered processes, keyed by connection."""

    def __init__(self, ttl: int = DISCOVERY_CACHE_TTL):
        self._ttl = ttl
        self._store: dict[str, tuple[float, list[DiscoveredProcess]]] = {}

    def get(self, config: ConnectionConfig) -> list[DiscoveredProcess] | None:
        """Return cached processes if still valid, else None."""
        key = _cache_key(config)
        entry = self._store.get(key)
        if entry is None:
            return None
        stored_at, processes = entry
        if time.time() - stored_at > self._ttl:
            logger.debug("discovery_cache_expired", key=key)
            del self._store[key]
            return None
        logger.debug("discovery_cache_hit", key=key, count=len(processes))
        return processes

    def store(self, config: ConnectionConfig, processes: list[DiscoveredProcess]) -> None:
        """Store discovery results with current timestamp."""
        key = _cache_key(config)
        self._store[key] = (time.time(), processes)
        logger.debug("discovery_cache_store", key=key, count=len(processes))

    def invalidate(self, config: ConnectionConfig) -> None:
        """Remove cached results for a connection."""
        key = _cache_key(config)
        self._store.pop(key, None)
        logger.debug("discovery_cache_invalidate", key=key)

    def clear(self) -> None:
        """Clear entire cache."""
        self._store.clear()

"""Tests for schema manager with caching."""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock

from biai.db.schema_manager import SchemaManager


@pytest.fixture
def mock_connector(sample_schema):
    connector = MagicMock()
    connector.get_schema_snapshot = AsyncMock(return_value=sample_schema)
    return connector


class TestSchemaManager:
    async def test_first_call_misses_cache(self, mock_connector):
        manager = SchemaManager(mock_connector, cache_ttl=60)
        assert not manager.is_cache_valid
        result = await manager.get_snapshot()
        assert result is not None
        mock_connector.get_schema_snapshot.assert_called_once()

    async def test_second_call_hits_cache(self, mock_connector):
        manager = SchemaManager(mock_connector, cache_ttl=60)
        await manager.get_snapshot()
        await manager.get_snapshot()
        assert mock_connector.get_schema_snapshot.call_count == 1

    async def test_force_refresh_bypasses_cache(self, mock_connector):
        manager = SchemaManager(mock_connector, cache_ttl=60)
        await manager.get_snapshot()
        await manager.get_snapshot(force_refresh=True)
        assert mock_connector.get_schema_snapshot.call_count == 2

    async def test_invalidate_cache(self, mock_connector):
        manager = SchemaManager(mock_connector, cache_ttl=60)
        await manager.get_snapshot()
        manager.invalidate_cache()
        assert not manager.is_cache_valid

    async def test_expired_cache(self, mock_connector):
        manager = SchemaManager(mock_connector, cache_ttl=0)  # expire immediately
        await manager.get_snapshot()
        time.sleep(0.01)
        assert not manager.is_cache_valid

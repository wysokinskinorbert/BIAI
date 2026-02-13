"""Integration test fixtures — real Docker PostgreSQL on port 5433.

Usage:
    docker compose -f docker-compose.dev.yml up -d postgres-test
    pytest -m integration -v
"""

import pytest
import pytest_asyncio

from biai.models.connection import ConnectionConfig, DBType
from biai.db.postgresql import PostgreSQLConnector
from biai.db.schema_manager import SchemaManager
from biai.db.query_executor import QueryExecutor


_PG_CONFIG = ConnectionConfig(
    db_type=DBType.POSTGRESQL,
    host="localhost",
    port=5433,
    database="biai_test",
    username="biai",
    password="biai123",
)


# ---------------------------------------------------------------------------
# PostgreSQL connector (function-scoped — avoids asyncpg event-loop mismatch)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def pg_connector():
    """Real PostgreSQL connector via Docker (port 5433).

    Function-scoped so each test gets its own connection on its own event loop.
    asyncpg pools are bound to the loop they were created on; sharing a
    session-scoped pool across per-test loops causes 'attached to a different
    loop' RuntimeError.
    """
    connector = PostgreSQLConnector(_PG_CONFIG)
    await connector.connect()
    yield connector
    await connector.disconnect()


@pytest.fixture(scope="session")
def pg_config():
    """ConnectionConfig for Docker PostgreSQL."""
    return _PG_CONFIG


@pytest.fixture
def schema_manager(pg_connector):
    """SchemaManager backed by real PostgreSQL."""
    return SchemaManager(pg_connector)


@pytest.fixture
def query_executor(pg_connector):
    """QueryExecutor backed by real PostgreSQL."""
    return QueryExecutor(pg_connector)

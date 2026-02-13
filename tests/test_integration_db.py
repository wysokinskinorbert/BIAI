"""Integration tests — DB layer on real Docker PostgreSQL.

Requires:
    docker compose -f docker-compose.dev.yml up -d postgres-test

Run:
    pytest tests/test_integration_db.py -m integration -v
"""

import pytest

from biai.models.connection import ConnectionConfig, DBType
from biai.models.query import QueryResult, QueryError
from biai.db.postgresql import PostgreSQLConnector
from biai.db.schema_manager import SchemaManager
from biai.db.query_executor import QueryExecutor

# Import fixtures from integration conftest
from tests.conftest_integration import pg_connector, pg_config, schema_manager, query_executor  # noqa: F401

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Connection tests
# ---------------------------------------------------------------------------

class TestConnection:
    async def test_connect_disconnect(self, pg_config):
        """Connector can connect and disconnect cleanly."""
        connector = PostgreSQLConnector(pg_config)
        await connector.connect()
        assert connector.is_connected
        await connector.disconnect()
        assert not connector.is_connected

    async def test_test_connection(self, pg_config):
        """test_connection() returns success and version string."""
        connector = PostgreSQLConnector(pg_config)
        ok, version = await connector.test_connection()
        assert ok is True
        assert "PostgreSQL" in version

    async def test_execute_simple_query(self, pg_connector):
        """Simple SELECT 1 returns expected result."""
        df = await pg_connector.execute_query("SELECT 1 AS val")
        assert len(df) == 1
        assert df.iloc[0]["val"] == 1

    async def test_server_version(self, pg_connector):
        """get_server_version() returns a version string."""
        version = await pg_connector.get_server_version()
        assert "PostgreSQL" in version or len(version) > 0


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestSchema:
    async def test_get_tables(self, pg_connector):
        """Connector returns seeded tables."""
        tables = await pg_connector.get_tables(schema="public")
        table_names = [t.name for t in tables]
        # Base tables from seed
        for expected in ["customers", "orders", "employees", "products"]:
            assert expected in table_names, f"Expected table '{expected}' not found"

    async def test_get_schema_snapshot(self, schema_manager):
        """SchemaManager returns full snapshot with tables and columns."""
        snapshot = await schema_manager.get_snapshot(schema="public", force_refresh=True)
        assert len(snapshot.tables) > 0
        # Check that tables have columns
        for table in snapshot.tables:
            assert len(table.columns) > 0

    async def test_get_table_names(self, schema_manager):
        """get_table_names() returns list of strings."""
        names = await schema_manager.get_table_names(schema="public")
        assert isinstance(names, list)
        assert len(names) > 0
        assert all(isinstance(n, str) for n in names)

    async def test_get_ddl_statements(self, schema_manager):
        """DDL statements are generated for all tables."""
        ddls = await schema_manager.get_ddl_statements(schema="public")
        assert len(ddls) > 0
        for ddl in ddls:
            assert "CREATE TABLE" in ddl

    async def test_schema_cache(self, schema_manager):
        """Schema caching works — second call uses cache."""
        await schema_manager.get_snapshot(schema="public", force_refresh=True)
        assert schema_manager.is_cache_valid
        snapshot2 = await schema_manager.get_snapshot(schema="public")
        assert snapshot2 is not None


# ---------------------------------------------------------------------------
# Query execution tests
# ---------------------------------------------------------------------------

class TestQueryExecution:
    async def test_execute_complex_query(self, pg_connector):
        """JOIN query returns expected data."""
        sql = """
        SELECT c.first_name, COUNT(o.order_id) AS order_count
        FROM customers c
        LEFT JOIN orders o ON c.customer_id = o.customer_id
        GROUP BY c.first_name
        ORDER BY order_count DESC
        LIMIT 5
        """
        df = await pg_connector.execute_query(sql)
        assert len(df) > 0
        assert "first_name" in df.columns
        assert "order_count" in df.columns

    async def test_query_executor_returns_result(self, query_executor):
        """QueryExecutor.execute() returns QueryResult for valid SQL."""
        result = await query_executor.execute("SELECT COUNT(*) AS cnt FROM customers")
        assert isinstance(result, QueryResult)
        assert result.row_count == 1
        assert result.columns == ["cnt"]
        assert result.rows[0][0] > 0

    async def test_query_executor_returns_error_for_bad_sql(self, query_executor):
        """QueryExecutor.execute() returns QueryError for invalid SQL."""
        result = await query_executor.execute("SELECT * FROM nonexistent_table_xyz")
        assert isinstance(result, QueryError)
        assert result.error_message != ""

    async def test_query_executor_dataframe(self, query_executor):
        """QueryResult.to_dataframe() produces usable DataFrame."""
        result = await query_executor.execute(
            "SELECT customer_id, first_name, email FROM customers LIMIT 10"
        )
        assert isinstance(result, QueryResult)
        df = result.to_dataframe()
        assert len(df) > 0
        assert "customer_id" in df.columns

    async def test_process_tables_exist(self, pg_connector):
        """Process tables from seed exist."""
        tables = await pg_connector.get_tables(schema="public")
        table_names = [t.name for t in tables]
        for expected in ["order_process_log", "sales_pipeline", "support_tickets", "approval_requests"]:
            assert expected in table_names, f"Process table '{expected}' missing"

    async def test_process_data_seeded(self, pg_connector):
        """Process tables contain seeded data."""
        for table in ["order_process_log", "sales_pipeline", "support_tickets", "approval_requests"]:
            df = await pg_connector.execute_query(f"SELECT COUNT(*) AS cnt FROM {table}")
            assert df.iloc[0]["cnt"] > 0, f"Table '{table}' has no data"

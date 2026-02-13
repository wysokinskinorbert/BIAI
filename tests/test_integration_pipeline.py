"""Integration tests — AI pipeline components on real Docker PostgreSQL.

Tests chart advisor, SQL validator, query executor, and schema trainer
with real data. Does NOT require Ollama (no LLM calls).

Requires:
    docker compose -f docker-compose.dev.yml up -d postgres-test

Run:
    pytest tests/test_integration_pipeline.py -m integration -v
"""

import pytest
import pandas as pd

from biai.ai.chart_advisor import ChartAdvisor
from biai.ai.chart_builder import build_plotly_figure
from biai.ai.echarts_builder import build_echarts_option, can_use_echarts
from biai.ai.sql_validator import SQLValidator
from biai.ai.training import SchemaTrainer
from biai.db.schema_manager import SchemaManager
from biai.db.query_executor import QueryExecutor
from biai.models.chart import ChartType
from biai.models.query import QueryResult

# Import fixtures from integration conftest
from tests.conftest_integration import pg_connector, pg_config, schema_manager, query_executor  # noqa: F401

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# ChartAdvisor on real query results
# ---------------------------------------------------------------------------

class TestChartAdvisorReal:
    async def test_bar_chart_from_order_counts(self, query_executor):
        """ChartAdvisor produces bar chart from customer order counts."""
        result = await query_executor.execute("""
            SELECT c.first_name, COUNT(o.order_id) AS order_count
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            GROUP BY c.first_name
            ORDER BY order_count DESC
            LIMIT 10
        """)
        assert isinstance(result, QueryResult)
        df = result.to_dataframe()

        advisor = ChartAdvisor()
        config = advisor.recommend("How many orders per customer?", result.sql, df)
        assert config.chart_type in (ChartType.BAR, ChartType.PIE, ChartType.TABLE)
        assert config.title != ""

    async def test_line_chart_from_monthly_data(self, query_executor):
        """ChartAdvisor produces line chart for time-series data."""
        result = await query_executor.execute("""
            SELECT TO_CHAR(order_date, 'YYYY-MM') AS month, COUNT(*) AS cnt
            FROM orders
            GROUP BY TO_CHAR(order_date, 'YYYY-MM')
            ORDER BY month
        """)
        assert isinstance(result, QueryResult)
        df = result.to_dataframe()

        advisor = ChartAdvisor()
        config = advisor.recommend("Show monthly order trend", result.sql, df)
        assert config.chart_type in (ChartType.LINE, ChartType.BAR, ChartType.AREA)

    async def test_echarts_option_builds(self, query_executor):
        """ECharts builder creates valid option from real data."""
        result = await query_executor.execute("""
            SELECT status, COUNT(*) AS cnt
            FROM orders
            GROUP BY status
        """)
        assert isinstance(result, QueryResult)
        df = result.to_dataframe()

        advisor = ChartAdvisor()
        config = advisor.recommend("Order status distribution", result.sql, df)

        if can_use_echarts(config.chart_type):
            option = build_echarts_option(config, df)
            assert option != {}
            assert "series" in option

    async def test_plotly_figure_builds(self, query_executor):
        """Plotly builder creates valid traces from real data."""
        result = await query_executor.execute("""
            SELECT first_name, email FROM customers LIMIT 5
        """)
        assert isinstance(result, QueryResult)
        df = result.to_dataframe()

        advisor = ChartAdvisor()
        config = advisor.recommend("Show customers", result.sql, df)
        traces, layout = build_plotly_figure(config, df)
        # May be empty (TABLE type) but should not crash
        assert isinstance(traces, list)
        assert isinstance(layout, dict)


# ---------------------------------------------------------------------------
# SQL Validator on real schema
# ---------------------------------------------------------------------------

class TestSQLValidatorReal:
    def test_valid_select(self):
        """Valid SELECT passes validation."""
        validator = SQLValidator(dialect="postgres")
        result = validator.validate(
            "SELECT customer_id, name FROM customers WHERE customer_id = 1"
        )
        assert result.is_valid

    def test_blocks_drop(self):
        """DROP TABLE is blocked."""
        validator = SQLValidator(dialect="postgres")
        result = validator.validate("DROP TABLE customers")
        assert not result.is_valid

    def test_blocks_delete(self):
        """DELETE is blocked."""
        validator = SQLValidator(dialect="postgres")
        result = validator.validate("DELETE FROM customers WHERE 1=1")
        assert not result.is_valid

    def test_transpiles_limit(self):
        """Validates SELECT with LIMIT."""
        validator = SQLValidator(dialect="postgres")
        result = validator.validate("SELECT * FROM customers LIMIT 10")
        assert result.is_valid


# ---------------------------------------------------------------------------
# SchemaTrainer on real snapshot
# ---------------------------------------------------------------------------

class TestSchemaTrainerReal:
    async def test_schema_trainer_trains(self, schema_manager):
        """SchemaTrainer can train on real schema without error."""
        from biai.ai.vanna_client import create_vanna_client
        from biai.config.constants import DEFAULT_MODEL

        try:
            vanna = create_vanna_client(
                model=DEFAULT_MODEL,
                ollama_host="http://localhost:11434",
                dialect="postgresql",
            )
        except Exception as exc:
            pytest.skip(f"Ollama not available: {exc}")

        vanna.reset_collections()

        trainer = SchemaTrainer(vanna)
        snapshot = await schema_manager.get_snapshot(schema="public", force_refresh=True)

        stats = trainer.train_full(schema=snapshot)
        assert stats["ddl"] > 0
        assert stats["ddl"] + stats.get("docs", 0) + stats.get("examples", 0) > 0


# ---------------------------------------------------------------------------
# QueryExecutor with aggregation
# ---------------------------------------------------------------------------

class TestQueryExecutorReal:
    async def test_aggregation_returns_numeric(self, query_executor):
        """Aggregation queries return numeric types (not Decimal)."""
        result = await query_executor.execute(
            "SELECT COUNT(*) AS cnt, AVG(order_id) AS avg_id FROM orders"
        )
        assert isinstance(result, QueryResult)
        df = result.to_dataframe()
        # After to_dataframe() coercion, numeric columns should be recognized
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        assert len(num_cols) > 0

    async def test_process_log_query(self, query_executor):
        """Order process log query returns expected columns."""
        result = await query_executor.execute("""
            SELECT from_status, to_status, AVG(duration_minutes) AS avg_dur
            FROM order_process_log
            GROUP BY from_status, to_status
            ORDER BY avg_dur DESC
            LIMIT 10
        """)
        assert isinstance(result, QueryResult)
        assert result.row_count > 0
        assert "from_status" in result.columns
        assert "avg_dur" in result.columns

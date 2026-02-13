"""Tests for data models."""

import pytest
from decimal import Decimal

from biai.models.query import QueryResult, SQLQuery, QueryError
from biai.models.connection import ConnectionConfig, DBType
from biai.models.chart import ChartConfig, ChartType


class TestQueryResult:
    def test_to_dataframe_basic(self):
        r = QueryResult(
            sql="SELECT 1",
            columns=["a", "b"],
            rows=[[1, 2], [3, 4]],
            row_count=2,
        )
        df = r.to_dataframe()
        assert list(df.columns) == ["a", "b"]
        assert len(df) == 2

    def test_to_dataframe_decimal_coercion(self):
        r = QueryResult(
            sql="SELECT 1",
            columns=["amount"],
            rows=[[Decimal("10.5")], [Decimal("20.3")]],
            row_count=2,
        )
        df = r.to_dataframe()
        assert df["amount"].dtype != object  # should be numeric

    def test_to_dataframe_empty(self):
        r = QueryResult(sql="SELECT 1", columns=[], rows=[], row_count=0)
        df = r.to_dataframe()
        assert df.empty

    def test_to_csv(self):
        r = QueryResult(
            sql="SELECT 1", columns=["x"], rows=[[1], [2]], row_count=2
        )
        csv = r.to_csv()
        assert "x" in csv
        assert "1" in csv


class TestConnectionConfig:
    def test_display_name_postgresql(self):
        c = ConnectionConfig(
            db_type=DBType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="test",
        )
        assert "postgresql" in c.display_name
        assert "localhost" in c.display_name

    def test_display_name_oracle_dsn(self):
        c = ConnectionConfig(
            db_type=DBType.ORACLE,
            dsn="mydsn_very_long_string_here_1234567890",
        )
        assert "oracle" in c.display_name
        assert "..." in c.display_name

    def test_get_oracle_dsn(self):
        c = ConnectionConfig(
            db_type=DBType.ORACLE, host="h", port=1521, database="XEPDB1"
        )
        assert c.get_oracle_dsn() == "h:1521/XEPDB1"

    def test_get_postgresql_dsn(self):
        c = ConnectionConfig(
            db_type=DBType.POSTGRESQL,
            host="h",
            port=5432,
            database="db",
            username="u",
            password="p",
        )
        assert "postgresql://u:p@h:5432/db" == c.get_postgresql_dsn()


class TestSQLQuery:
    def test_default_invalid(self):
        q = SQLQuery(sql="SELECT 1")
        assert not q.is_valid

    def test_with_error(self):
        q = SQLQuery(sql="BAD", validation_error="parse error")
        assert q.validation_error == "parse error"


class TestChartConfig:
    def test_defaults(self):
        c = ChartConfig()
        assert c.chart_type == ChartType.BAR
        assert c.y_columns == []

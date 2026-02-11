"""Tests for chart advisor and pipeline utilities."""

import pytest
import pandas as pd

from biai.ai.chart_advisor import ChartAdvisor, _generate_title
from biai.models.chart import ChartType


class TestChartAdvisor:
    """Test chart recommendation heuristics."""

    @pytest.fixture
    def advisor(self):
        return ChartAdvisor(vanna_client=None)

    def test_time_series_line(self, advisor, sample_dataframe):
        df = pd.DataFrame({
            "month": ["2024-01", "2024-02", "2024-03"],
            "revenue": [10000, 12000, 15000],
        })
        config = advisor.recommend("Show monthly revenue trend", "", df)
        assert config.chart_type == ChartType.LINE

    def test_proportion_pie(self, advisor):
        df = pd.DataFrame({
            "category": ["A", "B", "C"],
            "percentage": [40, 35, 25],
        })
        config = advisor.recommend("Show percentage breakdown by category", "", df)
        assert config.chart_type == ChartType.PIE

    def test_comparison_bar(self, advisor, sample_dataframe):
        config = advisor.recommend("Compare customers by revenue", "", sample_dataframe)
        assert config.chart_type == ChartType.BAR

    def test_scatter_correlation(self, advisor):
        df = pd.DataFrame({
            "price": [10, 20, 30, 40],
            "quantity": [100, 80, 60, 40],
        })
        config = advisor.recommend("Show correlation of price vs quantity", "", df)
        assert config.chart_type == ChartType.SCATTER

    def test_empty_data_table(self, advisor):
        df = pd.DataFrame()
        config = advisor.recommend("Show something", "", df)
        assert config.chart_type == ChartType.TABLE

    def test_single_column_table(self, advisor):
        df = pd.DataFrame({"name": ["Alice", "Bob"]})
        config = advisor.recommend("Show names", "", df)
        assert config.chart_type == ChartType.TABLE


class TestGenerateTitle:
    def test_short_question(self):
        assert _generate_title("Top customers?") == "Top customers"

    def test_long_question(self):
        long_q = "A" * 100
        title = _generate_title(long_q)
        assert len(title) <= 60

    def test_strips_punctuation(self):
        assert _generate_title("What are the sales?") == "What are the sales"

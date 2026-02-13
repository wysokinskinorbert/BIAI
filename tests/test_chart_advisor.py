"""Tests for chart advisor heuristics."""

import pytest
import pandas as pd

from biai.ai.chart_advisor import ChartAdvisor
from biai.models.chart import ChartConfig, ChartType


@pytest.fixture
def advisor():
    return ChartAdvisor()  # no vanna client needed for heuristics


class TestHeuristicRecommend:
    def test_time_series_returns_line(self, advisor):
        df = pd.DataFrame({"month": ["Jan", "Feb", "Mar"], "sales": [100, 200, 300]})
        config = advisor._heuristic_recommend(df, "show monthly sales trend")
        assert config.chart_type == ChartType.LINE

    def test_proportion_returns_pie(self, advisor):
        df = pd.DataFrame({"status": ["A", "B", "C"], "count": [10, 20, 30]})
        config = advisor._heuristic_recommend(df, "show status distribution")
        assert config.chart_type == ChartType.PIE

    def test_correlation_returns_scatter(self, advisor):
        df = pd.DataFrame({"height": [1, 2, 3], "weight": [4, 5, 6]})
        config = advisor._heuristic_recommend(df, "correlation of height vs weight")
        assert config.chart_type == ChartType.SCATTER

    def test_default_returns_bar(self, advisor):
        df = pd.DataFrame({"category": ["A", "B", "C"], "value": [1, 2, 3]})
        config = advisor._heuristic_recommend(df, "show categories")
        assert config.chart_type == ChartType.BAR

    def test_empty_returns_table(self, advisor):
        df = pd.DataFrame()
        config = advisor._heuristic_recommend(df, "anything")
        assert config.chart_type == ChartType.TABLE

    def test_single_column_returns_table(self, advisor):
        df = pd.DataFrame({"col": [1, 2, 3]})
        config = advisor._heuristic_recommend(df, "show data")
        assert config.chart_type == ChartType.TABLE

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

    def test_single_row_returns_table(self, advisor):
        df = pd.DataFrame({"metric": ["total"], "value": [42]})
        config = advisor._heuristic_recommend(df, "show total count")
        assert config.chart_type == ChartType.TABLE

    def test_funnel_detection(self, advisor):
        df = pd.DataFrame({
            "stage": ["Lead", "Qualified", "Proposal", "Won"],
            "count": [100, 60, 30, 10],
        })
        config = advisor._heuristic_recommend(df, "show sales funnel stages")
        assert config.chart_type == ChartType.FUNNEL

    def test_waterfall_detection(self, advisor):
        df = pd.DataFrame({
            "item": ["Revenue", "COGS", "Expenses", "Tax"],
            "amount": [1000, -400, -200, -100],
        })
        config = advisor._heuristic_recommend(df, "revenue breakdown by category")
        assert config.chart_type == ChartType.WATERFALL

    def test_grouped_bar_detection(self, advisor):
        df = pd.DataFrame({
            "category": ["A", "A", "B", "B", "C", "C"],
            "priority": ["High", "Low", "High", "Low", "High", "Low"],
            "count": [10, 5, 8, 3, 12, 7],
        })
        config = advisor._heuristic_recommend(df, "tickets by category and priority")
        assert config.chart_type == ChartType.BAR
        assert config.group_column == "priority"

    def test_area_detection(self, advisor):
        df = pd.DataFrame({"month": ["Jan", "Feb", "Mar"], "total": [100, 300, 600]})
        config = advisor._heuristic_recommend(df, "cumulative sales growth over time")
        assert config.chart_type == ChartType.AREA

    def test_horizontal_bar_for_many_categories(self, advisor):
        categories = [f"Cat_{i}" for i in range(15)]
        df = pd.DataFrame({"name": categories, "value": range(15)})
        config = advisor._heuristic_recommend(df, "show all categories")
        assert config.chart_type == ChartType.BAR
        assert config.horizontal is True

    def test_pie_polish_keywords(self, advisor):
        df = pd.DataFrame({"typ": ["A", "B", "C"], "wartosc": [10, 20, 30]})
        config = advisor._heuristic_recommend(df, "procentowy udzial typow")
        assert config.chart_type == ChartType.PIE

    def test_heatmap_auto_detection(self, advisor):
        rows = []
        for cat in ["A", "B", "C", "D"]:
            for pri in ["P1", "P2", "P3"]:
                rows.append({"category": cat, "priority": pri, "count": 5})
        df = pd.DataFrame(rows)
        config = advisor._heuristic_recommend(df, "tickets by category and priority")
        assert config.chart_type == ChartType.HEATMAP

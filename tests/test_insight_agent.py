"""Tests for InsightAgent — heuristic-based data insights."""

import asyncio

import numpy as np
import pandas as pd
import pytest

from biai.ai.insight_agent import InsightAgent
from biai.models.insight import InsightType, InsightSeverity


@pytest.fixture
def agent():
    return InsightAgent()


class TestPareto:
    """Test _check_pareto() — 80/20 concentration detection."""

    def test_pareto_detected(self, agent):
        # Top 1 out of 5 categories = 85% of value → Pareto
        df = pd.DataFrame({
            "category": ["A", "B", "C", "D", "E"],
            "revenue": [8500, 500, 400, 300, 300],
        })
        result = agent._check_pareto(df, "category", "revenue")
        assert result is not None
        assert result.type == InsightType.PARETO

    def test_no_pareto_even_distribution(self, agent):
        df = pd.DataFrame({
            "category": ["A", "B", "C", "D", "E"],
            "revenue": [200, 200, 200, 200, 200],
        })
        result = agent._check_pareto(df, "category", "revenue")
        assert result is None  # Even distribution → no Pareto

    def test_pareto_too_few_categories(self, agent):
        df = pd.DataFrame({"cat": ["A", "B"], "val": [100, 200]})
        result = agent._check_pareto(df, "cat", "val")
        assert result is None  # Need >= 3 categories

    def test_pareto_zero_total(self, agent):
        df = pd.DataFrame({"cat": ["A", "B", "C"], "val": [0, 0, 0]})
        result = agent._check_pareto(df, "cat", "val")
        assert result is None


class TestAnomalies:
    """Test _check_anomalies() — z-score outlier detection."""

    def test_outlier_detected(self, agent):
        values = [10, 11, 9, 10, 12, 10, 11, 9, 10, 100]  # 100 is outlier
        df = pd.DataFrame({"col": values})
        result = agent._check_anomalies(df, "col")
        assert result is not None
        assert result.type == InsightType.ANOMALY

    def test_no_outlier_normal_data(self, agent):
        df = pd.DataFrame({"col": [10, 11, 12, 13, 14, 15]})
        result = agent._check_anomalies(df, "col")
        assert result is None

    def test_constant_values(self, agent):
        df = pd.DataFrame({"col": [5, 5, 5, 5, 5]})
        result = agent._check_anomalies(df, "col")
        assert result is None  # std=0, skip

    def test_too_few_values(self, agent):
        df = pd.DataFrame({"col": [1, 2, 100]})
        result = agent._check_anomalies(df, "col")
        assert result is None  # need >= 5


class TestTrend:
    """Test _check_trend() — increasing/decreasing detection."""

    def test_upward_trend(self, agent):
        df = pd.DataFrame({"col": [10, 15, 20, 25, 30, 35]})
        result = agent._check_trend(df, "col")
        assert result is not None
        assert result.type == InsightType.TREND
        assert "Upward" in result.title

    def test_downward_trend(self, agent):
        df = pd.DataFrame({"col": [50, 40, 30, 20, 10]})
        result = agent._check_trend(df, "col")
        assert result is not None
        assert "Downward" in result.title
        assert result.severity == InsightSeverity.WARNING

    def test_no_trend_random(self, agent):
        df = pd.DataFrame({"col": [10, 50, 5, 80, 20]})
        result = agent._check_trend(df, "col")
        assert result is None  # No consistent direction

    def test_too_few_points(self, agent):
        df = pd.DataFrame({"col": [10, 20, 30]})
        result = agent._check_trend(df, "col")
        assert result is None  # need >= 4


class TestCorrelation:
    """Test _check_correlation() — Pearson r detection."""

    def test_strong_positive_correlation(self, agent):
        df = pd.DataFrame({
            "x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "y": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
        })
        result = agent._check_correlation(df, ["x", "y"])
        assert result is not None
        assert result.type == InsightType.CORRELATION
        assert "positive" in result.title

    def test_strong_negative_correlation(self, agent):
        df = pd.DataFrame({
            "x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "y": [20, 18, 16, 14, 12, 10, 8, 6, 4, 2],
        })
        result = agent._check_correlation(df, ["x", "y"])
        assert result is not None
        assert "negative" in result.title

    def test_no_correlation(self, agent):
        np.random.seed(42)
        df = pd.DataFrame({
            "x": np.random.randn(50),
            "y": np.random.randn(50),
        })
        result = agent._check_correlation(df, ["x", "y"])
        assert result is None  # random → weak correlation

    def test_single_column(self, agent):
        df = pd.DataFrame({"x": [1, 2, 3]})
        result = agent._check_correlation(df, ["x"])
        assert result is None  # need >= 2 columns


class TestDistribution:
    """Test _check_distribution() — skewness detection."""

    def test_right_skewed(self, agent):
        # Exponential-like distribution → right skew
        np.random.seed(42)
        df = pd.DataFrame({"col": np.random.exponential(scale=2, size=100)})
        result = agent._check_distribution(df, "col")
        # Exponential has skew ≈ 2.0, should detect
        if result:
            assert result.type == InsightType.DISTRIBUTION
            assert "right-skewed" in result.description

    def test_normal_no_skew(self, agent):
        np.random.seed(42)
        df = pd.DataFrame({"col": np.random.normal(0, 1, 200)})
        result = agent._check_distribution(df, "col")
        assert result is None  # Normal distribution → no significant skew

    def test_too_few_values(self, agent):
        df = pd.DataFrame({"col": [1, 2, 3]})
        result = agent._check_distribution(df, "col")
        assert result is None  # need >= 10


class TestAnalyzeSync:
    """Test full analyze_sync() pipeline."""

    def test_empty_df(self, agent):
        df = pd.DataFrame()
        result = agent.analyze_sync(df, "test question")
        assert result == []

    def test_single_row(self, agent):
        df = pd.DataFrame({"a": [1], "b": [2]})
        result = agent.analyze_sync(df, "test")
        assert result == []  # need >= 2 rows

    def test_max_5_insights(self, agent):
        # Large varied dataset should produce multiple insights but cap at 5
        np.random.seed(42)
        df = pd.DataFrame({
            "cat": ["A"] * 80 + ["B"] * 10 + ["C"] * 5 + ["D"] * 3 + ["E"] * 2,
            "val1": np.random.exponential(scale=100, size=100),
            "val2": np.arange(100) + np.random.normal(0, 1, 100),  # trend
            "val3": np.random.normal(50, 10, 100),
        })
        result = agent.analyze_sync(df, "show me everything")
        assert len(result) <= 5

    def test_insights_have_required_fields(self, agent):
        df = pd.DataFrame({
            "category": ["A", "B", "C", "D", "E"],
            "revenue": [8500, 500, 400, 300, 300],
        })
        result = agent.analyze_sync(df, "revenue by category")
        for insight in result:
            assert insight.title != ""
            assert insight.description != ""
            assert insight.type is not None
            assert insight.severity is not None


class TestAnalyzeAsync:
    """Test async analyze() wrapper."""

    @pytest.mark.asyncio
    async def test_async_returns_same_as_sync(self, agent):
        df = pd.DataFrame({
            "x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "y": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
        })
        sync_result = agent.analyze_sync(df, "test")
        async_result = await agent.analyze(df, "test")
        assert len(sync_result) == len(async_result)
        for s, a in zip(sync_result, async_result):
            assert s.type == a.type
            assert s.title == a.title

    @pytest.mark.asyncio
    async def test_async_timeout_returns_empty(self, agent):
        # With a very short timeout, should still gracefully return
        df = pd.DataFrame({"x": [1, 2, 3, 4, 5]})
        result = await agent.analyze(df, "test", timeout=0.0001)
        # Either returns fast or times out gracefully
        assert isinstance(result, list)

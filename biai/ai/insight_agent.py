"""Autonomous Insight Agent — heuristic-based data insights."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

from biai.models.insight import Insight, InsightType, InsightSeverity
from biai.utils.logger import get_logger

logger = get_logger(__name__)

_EXECUTOR = ThreadPoolExecutor(max_workers=2)

# Thresholds
_PARETO_THRESHOLD = 0.80  # top 20% produces 80% of value
_ZSCORE_THRESHOLD = 2.0
_CORRELATION_THRESHOLD = 0.7
_TREND_MIN_POINTS = 4


class InsightAgent:
    """Generates insights from query result DataFrames using statistical heuristics."""

    async def analyze(
        self, df: pd.DataFrame, question: str, timeout: float = 10.0,
    ) -> list[Insight]:
        """Async analysis — runs heuristics in a thread pool with timeout."""
        try:
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(_EXECUTOR, self.analyze_sync, df, question),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.warning("insight_analysis_timeout", timeout=timeout)
            return []
        except Exception as e:
            logger.error("insight_analysis_error", error=str(e))
            return []

    def analyze_sync(self, df: pd.DataFrame, question: str) -> list[Insight]:
        """Synchronous analysis — returns list of insights."""
        insights: list[Insight] = []

        if df.empty or len(df) < 2:
            return insights

        # Force numeric coercion on object columns (Decimal from DB)
        for col in df.select_dtypes(include=["object"]).columns:
            converted = pd.to_numeric(df[col], errors="coerce")
            if converted.notna().any():
                df[col] = converted

        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        cat_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

        # 1. Pareto analysis
        if num_cols and cat_cols:
            pareto = self._check_pareto(df, cat_cols[0], num_cols[0])
            if pareto:
                insights.append(pareto)

        # 2. Anomaly detection (z-score)
        for col in num_cols[:3]:
            anomaly = self._check_anomalies(df, col)
            if anomaly:
                insights.append(anomaly)

        # 3. Trend detection
        if len(num_cols) >= 1 and len(df) >= _TREND_MIN_POINTS:
            trend = self._check_trend(df, num_cols[0])
            if trend:
                insights.append(trend)

        # 4. Correlation
        if len(num_cols) >= 2:
            corr = self._check_correlation(df, num_cols)
            if corr:
                insights.append(corr)

        # 5. Distribution skew
        for col in num_cols[:2]:
            dist = self._check_distribution(df, col)
            if dist:
                insights.append(dist)

        return insights[:5]  # max 5 insights

    @staticmethod
    def _check_pareto(df: pd.DataFrame, cat_col: str, val_col: str) -> Insight | None:
        """Check for Pareto (80/20) distribution."""
        try:
            grouped = df.groupby(cat_col)[val_col].sum().sort_values(ascending=False)
            if len(grouped) < 3:
                return None
            total = grouped.sum()
            if total == 0:
                return None
            cumsum = grouped.cumsum()
            threshold_idx = (cumsum >= total * _PARETO_THRESHOLD).idxmax()
            top_count = list(grouped.index).index(threshold_idx) + 1
            top_pct = round(top_count / len(grouped) * 100)
            val_pct = round(cumsum[threshold_idx] / total * 100)

            if top_pct <= 30:
                return Insight(
                    type=InsightType.PARETO,
                    title=f"Pareto: {top_pct}% of {cat_col} = {val_pct}% of {val_col}",
                    description=(
                        f"Top {top_count} out of {len(grouped)} categories in '{cat_col}' "
                        f"account for {val_pct}% of total '{val_col}'. "
                        f"This follows a Pareto-like concentration pattern."
                    ),
                    severity=InsightSeverity.INFO,
                )
        except Exception:
            pass
        return None

    @staticmethod
    def _check_anomalies(df: pd.DataFrame, col: str) -> Insight | None:
        """Detect outliers using z-score."""
        try:
            series = df[col].dropna()
            if len(series) < 5:
                return None
            mean = series.mean()
            std = series.std()
            if std == 0:
                return None
            z_scores = ((series - mean) / std).abs()
            outliers = z_scores[z_scores > _ZSCORE_THRESHOLD]
            if len(outliers) > 0:
                pct = round(len(outliers) / len(series) * 100, 1)
                max_val = series[z_scores.idxmax()]
                return Insight(
                    type=InsightType.ANOMALY,
                    title=f"{len(outliers)} outliers in {col}",
                    description=(
                        f"Found {len(outliers)} values ({pct}%) in '{col}' "
                        f"that are more than {_ZSCORE_THRESHOLD} standard deviations from mean "
                        f"({mean:.1f}). Max outlier: {max_val:.1f}."
                    ),
                    severity=InsightSeverity.WARNING if pct > 5 else InsightSeverity.INFO,
                )
        except Exception:
            pass
        return None

    @staticmethod
    def _check_trend(df: pd.DataFrame, col: str) -> Insight | None:
        """Detect consistent increasing/decreasing trend.

        Skips columns that are strictly monotonic (sorted data artifact, not a real trend).
        """
        try:
            values = df[col].dropna().values
            if len(values) < _TREND_MIN_POINTS:
                return None
            diffs = np.diff(values)
            increasing = (diffs > 0).sum()
            decreasing = (diffs < 0).sum()
            total_diffs = len(diffs)

            # P6: Skip if data is strictly monotonic — likely sorted by this column,
            # not a real temporal trend (e.g. ORDER BY value ASC)
            if increasing == total_diffs or decreasing == total_diffs:
                return None

            if increasing / total_diffs > 0.75:
                change = round((values[-1] - values[0]) / max(abs(values[0]), 1) * 100, 1)
                return Insight(
                    type=InsightType.TREND,
                    title=f"Upward trend in {col} (+{change}%)",
                    description=(
                        f"'{col}' shows a consistent upward trend: "
                        f"{increasing}/{total_diffs} consecutive increases, "
                        f"from {values[0]:.1f} to {values[-1]:.1f} ({change:+.1f}%)."
                    ),
                    severity=InsightSeverity.INFO,
                )
            elif decreasing / total_diffs > 0.75:
                change = round((values[-1] - values[0]) / max(abs(values[0]), 1) * 100, 1)
                return Insight(
                    type=InsightType.TREND,
                    title=f"Downward trend in {col} ({change}%)",
                    description=(
                        f"'{col}' shows a consistent downward trend: "
                        f"{decreasing}/{total_diffs} consecutive decreases, "
                        f"from {values[0]:.1f} to {values[-1]:.1f} ({change:+.1f}%)."
                    ),
                    severity=InsightSeverity.WARNING,
                )
        except Exception:
            pass
        return None

    @staticmethod
    def _check_correlation(df: pd.DataFrame, num_cols: list[str]) -> Insight | None:
        """Check for strong correlations between numeric columns."""
        try:
            corr_matrix = df[num_cols].corr()
            # Find strongest non-self correlation
            best_r = 0.0
            best_pair = ("", "")
            for i, c1 in enumerate(num_cols):
                for j, c2 in enumerate(num_cols):
                    if i >= j:
                        continue
                    r = abs(corr_matrix.loc[c1, c2])
                    if r > best_r:
                        best_r = r
                        best_pair = (c1, c2)

            if best_r >= _CORRELATION_THRESHOLD:
                direction = "positive" if corr_matrix.loc[best_pair[0], best_pair[1]] > 0 else "negative"
                return Insight(
                    type=InsightType.CORRELATION,
                    title=f"Strong {direction} correlation: {best_pair[0]} ↔ {best_pair[1]}",
                    description=(
                        f"'{best_pair[0]}' and '{best_pair[1]}' have a strong "
                        f"{direction} correlation (r={best_r:.2f}). "
                        f"Changes in one column tend to be accompanied by "
                        f"{'similar' if direction == 'positive' else 'opposite'} changes in the other."
                    ),
                    severity=InsightSeverity.INFO,
                )
        except Exception:
            pass
        return None

    @staticmethod
    def _check_distribution(df: pd.DataFrame, col: str) -> Insight | None:
        """Check for skewed distribution."""
        try:
            series = df[col].dropna()
            if len(series) < 10:
                return None
            skew = series.skew()
            if abs(skew) > 1.5:
                direction = "right-skewed (long tail of high values)" if skew > 0 else "left-skewed (long tail of low values)"
                return Insight(
                    type=InsightType.DISTRIBUTION,
                    title=f"Skewed distribution in {col}",
                    description=(
                        f"'{col}' has a {direction} with skewness={skew:.2f}. "
                        f"Median ({series.median():.1f}) differs significantly from "
                        f"mean ({series.mean():.1f}), suggesting the average is "
                        f"{'pulled up' if skew > 0 else 'pulled down'} by extreme values."
                    ),
                    severity=InsightSeverity.INFO,
                )
        except Exception:
            pass
        return None

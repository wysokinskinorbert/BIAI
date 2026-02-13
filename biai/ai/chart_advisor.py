"""Chart type advisor using LLM + heuristics."""

import json

import pandas as pd

from biai.models.chart import ChartConfig, ChartEngine, ChartType
from biai.ai.echarts_builder import can_use_echarts
from biai.ai.prompt_templates import CHART_ADVISOR_PROMPT
from biai.utils.logger import get_logger

logger = get_logger(__name__)


class ChartAdvisor:
    """Recommends chart type and configuration based on data characteristics."""

    def __init__(self, vanna_client=None):
        self._vanna = vanna_client

    def recommend(
        self,
        question: str,
        sql: str,
        df: pd.DataFrame,
    ) -> ChartConfig:
        """Recommend chart configuration for given data."""
        # Try heuristic-based recommendation first
        config = self._heuristic_recommend(df, question)

        # If LLM available, try LLM-based recommendation
        if self._vanna and len(df) > 0:
            llm_config = self._llm_recommend(question, sql, df)
            if llm_config:
                config = llm_config

        # Auto-select engine: simple types → ECharts, complex → Plotly
        config.engine = (
            ChartEngine.ECHARTS if can_use_echarts(config.chart_type) else ChartEngine.PLOTLY
        )
        return config

    def _heuristic_recommend(self, df: pd.DataFrame, question: str) -> ChartConfig:
        """Heuristic-based chart recommendation."""
        if df.empty or len(df.columns) < 2:
            return ChartConfig(chart_type=ChartType.TABLE)

        question_lower = question.lower()
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        cat_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

        # Time series detection
        time_keywords = ["trend", "monthly", "daily", "weekly", "yearly", "over time", "time"]
        is_time = any(kw in question_lower for kw in time_keywords)
        has_date_col = any(
            "date" in c.lower() or "month" in c.lower() or "year" in c.lower()
            for c in df.columns
        )

        if (is_time or has_date_col) and num_cols:
            x_col = cat_cols[0] if cat_cols else df.columns[0]
            # Separate index-like numeric cols from value cols
            index_patterns = {"month", "year", "day", "week", "quarter", "period", "date", "id"}
            value_cols = [c for c in num_cols if not any(p in c.lower() for p in index_patterns)]
            if not value_cols:
                value_cols = num_cols[-1:]  # fallback: last numeric column is likely the value
            # Never include x_col in y_cols
            y_cols = [c for c in value_cols if c != x_col][:3]
            if not y_cols:
                y_cols = [num_cols[-1]]

            # Area chart for cumulative/stacked data
            area_keywords = ["cumulative", "stacked", "growth", "total over", "accumulated"]
            if any(kw in question_lower for kw in area_keywords):
                return ChartConfig(
                    chart_type=ChartType.AREA,
                    x_column=x_col,
                    y_columns=y_cols,
                    title=_generate_title(question),
                )

            return ChartConfig(
                chart_type=ChartType.LINE,
                x_column=x_col,
                y_columns=y_cols,
                title=_generate_title(question),
            )

        # Proportion detection
        proportion_keywords = ["percentage", "share", "distribution", "breakdown", "proportion"]
        is_proportion = any(kw in question_lower for kw in proportion_keywords)

        if is_proportion and cat_cols and num_cols and len(df) <= 10:
            return ChartConfig(
                chart_type=ChartType.PIE,
                x_column=cat_cols[0],
                y_columns=[num_cols[0]],
                title=_generate_title(question),
            )

        # Scatter for correlation
        if len(num_cols) >= 2 and ("correlation" in question_lower or "vs" in question_lower):
            return ChartConfig(
                chart_type=ChartType.SCATTER,
                x_column=num_cols[0],
                y_columns=[num_cols[1]],
                title=_generate_title(question),
            )

        # Heatmap: 2+ categorical + 1 numeric, matrix-like data
        heatmap_keywords = ["heatmap", "matrix", "correlation", "cross-tab", "pivot"]
        if (
            len(cat_cols) >= 2
            and len(num_cols) >= 1
            and len(df) > 3
            and any(kw in question_lower for kw in heatmap_keywords)
        ):
            return ChartConfig(
                chart_type=ChartType.HEATMAP,
                x_column=cat_cols[0],
                y_columns=num_cols[:1],
                title=_generate_title(question),
            )

        # Timeline: date column + category
        timeline_keywords = ["timeline", "gantt", "schedule", "milestones", "events"]
        if any(kw in question_lower for kw in timeline_keywords) and has_date_col:
            date_col = next(
                (c for c in df.columns if any(p in c.lower() for p in ("date", "time", "month", "year"))),
                cat_cols[0] if cat_cols else df.columns[0],
            )
            label_col = next(
                (c for c in cat_cols if c != date_col),
                num_cols[0] if num_cols else df.columns[0],
            )
            return ChartConfig(
                chart_type=ChartType.TIMELINE,
                x_column=date_col,
                y_columns=[label_col],
                title=_generate_title(question),
            )

        # Sankey: flow/funnel with source -> target -> value
        sankey_keywords = ["flow", "funnel", "transition", "from to", "sankey"]
        if any(kw in question_lower for kw in sankey_keywords) and len(df.columns) >= 3:
            return ChartConfig(
                chart_type=ChartType.SANKEY,
                x_column=df.columns[0],
                y_columns=[df.columns[1], df.columns[2]],
                title=_generate_title(question),
            )

        # Default: bar chart (categories + numbers)
        if cat_cols and num_cols:
            x_col = cat_cols[0]
            y_cols = [c for c in num_cols if c != x_col][:3]
            if y_cols:
                return ChartConfig(
                    chart_type=ChartType.BAR,
                    x_column=x_col,
                    y_columns=y_cols,
                    title=_generate_title(question),
                )

        # All-numeric columns: use first column as x-axis (ID/label), rest as y
        if len(num_cols) >= 2:
            return ChartConfig(
                chart_type=ChartType.BAR,
                x_column=num_cols[0],
                y_columns=num_cols[1:4],
                title=_generate_title(question),
            )

        # Fallback to table
        return ChartConfig(chart_type=ChartType.TABLE, title=_generate_title(question))

    def _llm_recommend(self, question: str, sql: str, df: pd.DataFrame) -> ChartConfig | None:
        """LLM-based chart recommendation."""
        try:
            sample = df.head(5).to_string(index=False)
            prompt = CHART_ADVISOR_PROMPT.format(
                question=question,
                sql=sql,
                columns=", ".join(df.columns),
                sample_data=sample,
                row_count=len(df),
            )

            response = self._vanna.submit_prompt(prompt)
            if not response:
                return None

            # Parse JSON response
            # Find JSON in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start == -1 or end == 0:
                return None

            data = json.loads(response[start:end])

            chart_type = ChartType(data.get("chart_type", "bar"))
            return ChartConfig(
                chart_type=chart_type,
                x_column=data.get("x_column"),
                y_columns=data.get("y_columns", []),
                title=data.get("title", _generate_title(question)),
            )
        except Exception as e:
            logger.warning("llm_chart_advisor_failed", error=str(e))
            return None


def _generate_title(question: str) -> str:
    """Generate chart title from question."""
    title = question.strip().rstrip("?").rstrip(".")
    if len(title) > 60:
        title = title[:57] + "..."
    return title

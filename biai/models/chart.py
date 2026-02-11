"""Chart configuration models."""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class ChartType(str, Enum):
    """Supported chart types."""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"
    HEATMAP = "heatmap"
    TABLE = "table"  # fallback: no chart, just table


class ChartLibrary(str, Enum):
    """Chart rendering library."""
    ECHARTS = "echarts"
    PLOTLY = "plotly"


class ChartConfig(BaseModel):
    """Chart configuration for rendering."""
    chart_type: ChartType = ChartType.BAR
    library: ChartLibrary = ChartLibrary.ECHARTS
    title: str = ""
    x_column: str | None = None
    y_columns: list[str] = Field(default_factory=list)
    group_column: str | None = None
    show_legend: bool = True
    show_labels: bool = False


class EChartsOption(BaseModel):
    """ECharts option configuration (partial - extends at render)."""
    model_config = {"arbitrary_types_allowed": True}

    option: dict[str, Any] = Field(default_factory=dict)

    @staticmethod
    def dark_theme_base() -> dict[str, Any]:
        """Base dark theme configuration for ECharts."""
        return {
            "backgroundColor": "transparent",
            "textStyle": {"color": "#e0e0e0"},
            "title": {
                "textStyle": {"color": "#ffffff"},
                "subtextStyle": {"color": "#aaaaaa"},
            },
            "legend": {"textStyle": {"color": "#cccccc"}},
            "tooltip": {
                "backgroundColor": "rgba(30, 30, 30, 0.9)",
                "borderColor": "#555",
                "textStyle": {"color": "#e0e0e0"},
            },
            "xAxis": {
                "axisLine": {"lineStyle": {"color": "#555"}},
                "axisLabel": {"color": "#aaa"},
                "splitLine": {"lineStyle": {"color": "#333"}},
            },
            "yAxis": {
                "axisLine": {"lineStyle": {"color": "#555"}},
                "axisLabel": {"color": "#aaa"},
                "splitLine": {"lineStyle": {"color": "#333"}},
            },
        }

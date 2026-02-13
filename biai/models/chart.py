"""Chart configuration models."""

from enum import Enum
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
    PROCESS_FLOW = "process_flow"
    TIMELINE = "timeline"
    SANKEY = "sankey"


class ChartEngine(str, Enum):
    """Chart rendering engine."""
    PLOTLY = "plotly"
    ECHARTS = "echarts"


class ChartConfig(BaseModel):
    """Chart configuration for rendering."""
    chart_type: ChartType = ChartType.BAR
    title: str = ""
    x_column: str | None = None
    y_columns: list[str] = Field(default_factory=list)
    group_column: str | None = None
    show_legend: bool = True
    show_labels: bool = False
    engine: ChartEngine = ChartEngine.ECHARTS



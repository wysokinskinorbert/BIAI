"""Chart state for dashboard visualization."""

from typing import Any

import reflex as rx
import plotly.graph_objects as go


class ChartState(rx.State):
    """Manages chart configuration and data for the dashboard."""

    # Plotly figure stored as dict (JSON-serializable, must be public for Reflex tracking)
    plotly_fig_data: dict = {}
    show_plotly: bool = False

    # Chart info
    chart_title: str = ""

    # Version counter – forces React key change → Plotly component re-mount
    chart_version: int = 0

    def set_plotly(self, data: list[dict], layout: dict[str, Any], title: str = ""):
        self.plotly_fig_data = {"data": data, "layout": layout}
        self.show_plotly = True
        self.chart_title = title
        self.chart_version += 1

    def clear_chart(self):
        self.plotly_fig_data = {}
        self.show_plotly = False
        self.chart_title = ""
        self.chart_version += 1

    @rx.var
    def plotly_figure(self) -> go.Figure:
        """Construct Plotly Figure from stored dict for rendering."""
        if self.plotly_fig_data:
            return go.Figure(self.plotly_fig_data)
        return go.Figure()

"""Chart state for dashboard visualization."""

from typing import Any

import reflex as rx
import plotly.graph_objects as go


class ChartState(rx.State):
    """Manages chart configuration and data for the dashboard."""

    # Plotly figure stored as dict (JSON-serializable, must be public for Reflex tracking)
    plotly_fig_data: dict = {}
    show_plotly: bool = False

    # ECharts option dict (JSON-serializable)
    echarts_option: dict = {}
    show_echarts: bool = False

    # Engine selector: "plotly" or "echarts"
    chart_engine: str = "echarts"

    # Chart info
    chart_title: str = ""
    data_row_count: int = 0

    # Version counter – forces React key change → component re-mount
    chart_version: int = 0

    # Fullscreen dialog
    show_fullscreen: bool = False

    def set_plotly(self, data: list[dict], layout: dict[str, Any], title: str = ""):
        self.plotly_fig_data = {"data": data, "layout": layout}
        self.show_plotly = True
        self.show_echarts = False
        self.chart_engine = "plotly"
        self.chart_title = title
        self.chart_version += 1

    def set_echarts(self, option: dict, title: str = "", row_count: int = 0):
        self.echarts_option = option
        self.show_echarts = True
        self.show_plotly = False
        self.chart_engine = "echarts"
        self.chart_title = title
        self.data_row_count = row_count
        self.chart_version += 1

    def clear_chart(self):
        self.plotly_fig_data = {}
        self.echarts_option = {}
        self.show_plotly = False
        self.show_echarts = False
        self.chart_engine = "echarts"
        self.chart_title = ""
        self.chart_version += 1

    def toggle_fullscreen(self):
        self.show_fullscreen = not self.show_fullscreen

    @rx.var
    def has_chart(self) -> bool:
        return self.show_plotly or self.show_echarts

    @rx.var
    def chart_height(self) -> str:
        """Dynamic chart height based on data complexity."""
        n = self.data_row_count
        if n <= 3:
            return "250px"
        if n <= 8:
            return "320px"
        if n <= 15:
            return "380px"
        return "450px"

    @rx.var
    def plotly_figure(self) -> go.Figure:
        """Construct Plotly Figure from stored dict for rendering."""
        if self.plotly_fig_data:
            return go.Figure(self.plotly_fig_data)
        return go.Figure()

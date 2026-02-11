"""Chart state for dashboard visualization."""

from typing import Any
import reflex as rx


class ChartState(rx.State):
    """Manages chart configuration and data for the dashboard."""

    # ECharts
    echarts_option: dict[str, Any] = {}
    show_echarts: bool = False

    # Plotly
    plotly_data: list[dict] = []
    plotly_layout: dict[str, Any] = {}
    show_plotly: bool = False

    # Chart info
    chart_type: str = ""
    chart_title: str = ""

    # Fullscreen
    is_fullscreen: bool = False

    def set_echarts(self, option: dict[str, Any], title: str = ""):
        self.echarts_option = option
        self.show_echarts = True
        self.show_plotly = False
        self.chart_type = "echarts"
        self.chart_title = title

    def set_plotly(self, data: list[dict], layout: dict[str, Any], title: str = ""):
        self.plotly_data = data
        self.plotly_layout = layout
        self.show_plotly = True
        self.show_echarts = False
        self.chart_type = "plotly"
        self.chart_title = title

    def clear_chart(self):
        self.echarts_option = {}
        self.plotly_data = []
        self.plotly_layout = {}
        self.show_echarts = False
        self.show_plotly = False
        self.chart_type = ""
        self.chart_title = ""

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen

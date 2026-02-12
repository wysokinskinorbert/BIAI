"""Chart state for dashboard visualization."""

from typing import Any
import reflex as rx
import plotly.graph_objects as go


class ChartState(rx.State):
    """Manages chart configuration and data for the dashboard."""

    # Plotly figure stored as dict (serializable)
    _plotly_fig_dict: dict[str, Any] = {}
    show_plotly: bool = False

    # Chart info
    chart_type: str = ""
    chart_title: str = ""

    # Fullscreen
    is_fullscreen: bool = False

    def set_plotly(self, data: list[dict], layout: dict[str, Any], title: str = ""):
        self._plotly_fig_dict = {"data": data, "layout": layout}
        self.show_plotly = True
        self.chart_type = "plotly"
        self.chart_title = title

    def clear_chart(self):
        self._plotly_fig_dict = {}
        self.show_plotly = False
        self.chart_type = ""
        self.chart_title = ""

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen

    @rx.var
    def plotly_figure(self) -> go.Figure:
        """Construct Plotly Figure from stored dict for rendering."""
        if self._plotly_fig_dict:
            return go.Figure(self._plotly_fig_dict)
        return go.Figure()

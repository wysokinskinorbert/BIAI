"""Dashboard Builder state — manages widgets, layout, and persistence."""

from typing import Any

import reflex as rx

from biai.utils.dashboard_storage import DashboardStorage


class DashboardState(rx.State):
    """Manages dashboard widgets and their grid layout."""

    # Widget data: list of widget configs
    widgets: list[dict[str, Any]] = []

    # Grid layout: list of {i, x, y, w, h} dicts
    layout: list[dict[str, Any]] = []

    # Dashboard metadata
    dashboard_name: str = "My Dashboard"
    is_edit_mode: bool = True

    # Available saved dashboards
    saved_dashboards: list[dict] = []

    # UI state
    show_widget_palette: bool = False
    show_save_dialog: bool = False
    save_name: str = ""

    def set_save_name(self, value: str):
        self.save_name = value

    def set_show_save_dialog(self, value: bool):
        self.show_save_dialog = value

    def toggle_edit_mode(self):
        self.is_edit_mode = not self.is_edit_mode

    def toggle_widget_palette(self):
        self.show_widget_palette = not self.show_widget_palette

    def on_layout_change(self, new_layout: list[dict]):
        """Handle grid layout change from react-grid-layout."""
        self.layout = new_layout

    def add_widget(self, widget_type: str):
        """Add a new widget to the dashboard."""
        widget_id = DashboardStorage.generate_widget_id()

        # Default titles by type
        titles = {
            "chart": "New Chart",
            "table": "Data Table",
            "kpi": "KPI Metric",
            "text": "Text Note",
            "insight": "Insight",
        }

        widget = {
            "id": widget_id,
            "widget_type": widget_type,
            "title": titles.get(widget_type, "Widget"),
            "subtitle": "",
            "content": "",
            "echarts_option": {},
            "kpi_value": "—",
            "kpi_label": "",
            "insight_title": "",
            "insight_description": "",
            "query": "",
        }
        self.widgets.append(widget)

        # Add to grid layout (place at bottom)
        max_y = 0
        for item in self.layout:
            bottom = item.get("y", 0) + item.get("h", 3)
            if bottom > max_y:
                max_y = bottom

        default_sizes = {
            "chart": {"w": 6, "h": 4},
            "table": {"w": 12, "h": 3},
            "kpi": {"w": 3, "h": 2},
            "text": {"w": 4, "h": 2},
            "insight": {"w": 4, "h": 2},
        }
        size = default_sizes.get(widget_type, {"w": 6, "h": 3})

        self.layout.append({
            "i": widget_id,
            "x": 0,
            "y": max_y,
            "w": size["w"],
            "h": size["h"],
        })

    def remove_widget(self, widget_id: str):
        """Remove widget from dashboard."""
        self.widgets = [w for w in self.widgets if w.get("id") != widget_id]
        self.layout = [l for l in self.layout if l.get("i") != widget_id]

    def update_widget(self, widget_id: str, updates: dict):
        """Update widget config."""
        for i, w in enumerate(self.widgets):
            if w.get("id") == widget_id:
                w.update(updates)
                self.widgets[i] = w
                break

    def add_chart_widget(self, title: str, echarts_option: dict):
        """Add a pre-configured chart widget from a query result."""
        widget_id = DashboardStorage.generate_widget_id()
        self.widgets.append({
            "id": widget_id,
            "widget_type": "chart",
            "title": title,
            "subtitle": "",
            "echarts_option": echarts_option,
            "content": "",
            "kpi_value": "",
            "kpi_label": "",
            "insight_title": "",
            "insight_description": "",
            "query": "",
        })
        max_y = max((l.get("y", 0) + l.get("h", 0) for l in self.layout), default=0)
        self.layout.append({
            "i": widget_id, "x": 0, "y": max_y, "w": 6, "h": 4,
        })

    def add_kpi_widget(self, label: str, value: str):
        """Add a KPI widget."""
        widget_id = DashboardStorage.generate_widget_id()
        self.widgets.append({
            "id": widget_id,
            "widget_type": "kpi",
            "title": label,
            "subtitle": "",
            "kpi_value": value,
            "kpi_label": label,
            "echarts_option": {},
            "content": "",
            "insight_title": "",
            "insight_description": "",
            "query": "",
        })
        max_y = max((l.get("y", 0) + l.get("h", 0) for l in self.layout), default=0)
        self.layout.append({
            "i": widget_id, "x": 0, "y": max_y, "w": 3, "h": 2,
        })

    # --- Persistence ---

    def save_dashboard(self):
        """Save current dashboard."""
        name = self.save_name or self.dashboard_name
        DashboardStorage.save(name, self.widgets, self.layout)
        self.dashboard_name = name
        self.show_save_dialog = False
        self.saved_dashboards = DashboardStorage.list_dashboards()

    def load_dashboard(self, name: str):
        """Load a saved dashboard."""
        data = DashboardStorage.load(name)
        if data:
            self.widgets = data.get("widgets", [])
            self.layout = data.get("layout", [])
            self.dashboard_name = data.get("name", name)

    def delete_dashboard(self, name: str):
        DashboardStorage.delete(name)
        self.saved_dashboards = DashboardStorage.list_dashboards()

    def refresh_saved_list(self):
        self.saved_dashboards = DashboardStorage.list_dashboards()

    @rx.var
    def has_widgets(self) -> bool:
        return len(self.widgets) > 0

    @rx.var
    def widget_count(self) -> int:
        return len(self.widgets)

"""Dashboard Builder state — manages widgets, layout, and persistence."""

from typing import Any

import reflex as rx

from biai.utils.dashboard_storage import DashboardStorage


# Pre-defined dashboard templates
DASHBOARD_TEMPLATES: list[dict[str, Any]] = [
    {
        "name": "AI Process Report",
        "description": "Process flow analysis with KPIs, charts, and AI insights",
        "icon": "workflow",
        "widgets": [
            {"widget_type": "kpi", "title": "Total Processes", "kpi_value": "—", "kpi_label": "Discovered Processes"},
            {"widget_type": "kpi", "title": "Avg Duration", "kpi_value": "—", "kpi_label": "Avg Duration (min)"},
            {"widget_type": "kpi", "title": "Bottlenecks", "kpi_value": "—", "kpi_label": "Bottleneck Steps"},
            {"widget_type": "chart", "title": "Process Flow Overview"},
            {"widget_type": "chart", "title": "Step Duration Breakdown"},
            {"widget_type": "insight", "title": "AI Analysis", "insight_title": "Key Finding", "insight_description": "Ask AI to analyze your business processes — insights will appear here."},
            {"widget_type": "table", "title": "Process Details"},
            {"widget_type": "text", "title": "Summary", "content": "## Process Analysis Report\n\nUse the chat to ask about your business processes. Results from AI queries will populate these widgets.\n\n**Example queries:**\n- Show all business processes\n- What are the bottleneck steps?\n- Compare process durations"},
        ],
        "layout": [
            {"w": 4, "h": 2, "x": 0, "y": 0},
            {"w": 4, "h": 2, "x": 4, "y": 0},
            {"w": 4, "h": 2, "x": 8, "y": 0},
            {"w": 7, "h": 5, "x": 0, "y": 2},
            {"w": 5, "h": 5, "x": 7, "y": 2},
            {"w": 4, "h": 3, "x": 0, "y": 7},
            {"w": 8, "h": 3, "x": 4, "y": 7},
            {"w": 12, "h": 2, "x": 0, "y": 10},
        ],
    },
    {
        "name": "Sales Overview",
        "description": "Revenue KPI, sales chart, and text note",
        "icon": "trending-up",
        "widgets": [
            {"widget_type": "kpi", "title": "Total Revenue", "kpi_value": "—", "kpi_label": "Total Revenue"},
            {"widget_type": "kpi", "title": "Order Count", "kpi_value": "—", "kpi_label": "Orders"},
            {"widget_type": "kpi", "title": "Avg Order Value", "kpi_value": "—", "kpi_label": "Avg Value"},
            {"widget_type": "chart", "title": "Sales Trend"},
            {"widget_type": "text", "title": "Notes", "content": "Add your analysis notes here."},
        ],
        "layout": [
            {"w": 4, "h": 2, "x": 0, "y": 0},
            {"w": 4, "h": 2, "x": 4, "y": 0},
            {"w": 4, "h": 2, "x": 8, "y": 0},
            {"w": 8, "h": 4, "x": 0, "y": 2},
            {"w": 4, "h": 4, "x": 8, "y": 2},
        ],
    },
    {
        "name": "Data Analysis",
        "description": "Two charts side by side with insights",
        "icon": "bar-chart-3",
        "widgets": [
            {"widget_type": "chart", "title": "Chart 1"},
            {"widget_type": "chart", "title": "Chart 2"},
            {"widget_type": "insight", "title": "Key Insight", "insight_title": "Finding", "insight_description": "Add insight from your analysis."},
            {"widget_type": "table", "title": "Data Table"},
        ],
        "layout": [
            {"w": 6, "h": 4, "x": 0, "y": 0},
            {"w": 6, "h": 4, "x": 6, "y": 0},
            {"w": 4, "h": 2, "x": 0, "y": 4},
            {"w": 8, "h": 3, "x": 4, "y": 4},
        ],
    },
    {
        "name": "KPI Dashboard",
        "description": "Six KPI metrics with a summary chart",
        "icon": "hash",
        "widgets": [
            {"widget_type": "kpi", "title": "Metric 1", "kpi_value": "—", "kpi_label": "Metric 1"},
            {"widget_type": "kpi", "title": "Metric 2", "kpi_value": "—", "kpi_label": "Metric 2"},
            {"widget_type": "kpi", "title": "Metric 3", "kpi_value": "—", "kpi_label": "Metric 3"},
            {"widget_type": "kpi", "title": "Metric 4", "kpi_value": "—", "kpi_label": "Metric 4"},
            {"widget_type": "kpi", "title": "Metric 5", "kpi_value": "—", "kpi_label": "Metric 5"},
            {"widget_type": "kpi", "title": "Metric 6", "kpi_value": "—", "kpi_label": "Metric 6"},
            {"widget_type": "chart", "title": "Summary Chart"},
        ],
        "layout": [
            {"w": 2, "h": 2, "x": 0, "y": 0},
            {"w": 2, "h": 2, "x": 2, "y": 0},
            {"w": 2, "h": 2, "x": 4, "y": 0},
            {"w": 2, "h": 2, "x": 6, "y": 0},
            {"w": 2, "h": 2, "x": 8, "y": 0},
            {"w": 2, "h": 2, "x": 10, "y": 0},
            {"w": 12, "h": 4, "x": 0, "y": 2},
        ],
    },
]


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

    # Template picker
    show_template_picker: bool = False

    # Default dashboard (shown on main page)
    default_dashboard_name: str = ""
    default_widgets: list[dict[str, Any]] = []
    default_layout: list[dict[str, Any]] = []

    # Widget editing
    editing_widget_id: str = ""
    edit_title: str = ""
    edit_content: str = ""
    edit_kpi_value: str = ""
    edit_kpi_label: str = ""
    edit_insight_title: str = ""
    edit_insight_description: str = ""

    def set_save_name(self, value: str):
        self.save_name = value

    def set_show_save_dialog(self, value: bool):
        self.show_save_dialog = value

    def set_edit_title(self, value: str):
        self.edit_title = value

    def set_edit_content(self, value: str):
        self.edit_content = value

    def set_edit_kpi_value(self, value: str):
        self.edit_kpi_value = value

    def set_edit_kpi_label(self, value: str):
        self.edit_kpi_label = value

    def set_edit_insight_title(self, value: str):
        self.edit_insight_title = value

    def set_edit_insight_description(self, value: str):
        self.edit_insight_description = value

    def toggle_edit_mode(self):
        self.is_edit_mode = not self.is_edit_mode

    def toggle_widget_palette(self):
        self.show_widget_palette = not self.show_widget_palette

    def set_show_template_picker(self, value: bool):
        self.show_template_picker = value

    def load_template(self, template_index: int):
        """Load a dashboard template by index."""
        if template_index < 0 or template_index >= len(DASHBOARD_TEMPLATES):
            return
        tpl = DASHBOARD_TEMPLATES[template_index]
        self.widgets = []
        self.layout = []
        for i, wt in enumerate(tpl["widgets"]):
            wid = DashboardStorage.generate_widget_id()
            widget = {
                "id": wid,
                "widget_type": wt.get("widget_type", "text"),
                "title": wt.get("title", "Widget"),
                "subtitle": "",
                "content": wt.get("content", ""),
                "echarts_option": {},
                "kpi_value": wt.get("kpi_value", "—"),
                "kpi_label": wt.get("kpi_label", ""),
                "insight_title": wt.get("insight_title", ""),
                "insight_description": wt.get("insight_description", ""),
                "query": "",
            }
            self.widgets.append(widget)
            lt = tpl["layout"][i] if i < len(tpl["layout"]) else {"w": 6, "h": 3, "x": 0, "y": i * 3}
            self.layout.append({"i": wid, **lt})
        self.dashboard_name = tpl["name"]
        self.show_template_picker = False

    def start_edit_widget(self, widget_id: str):
        """Open edit dialog for a widget."""
        for w in self.widgets:
            if w.get("id") == widget_id:
                self.editing_widget_id = widget_id
                self.edit_title = w.get("title", "")
                self.edit_content = w.get("content", "")
                self.edit_kpi_value = w.get("kpi_value", "")
                self.edit_kpi_label = w.get("kpi_label", "")
                self.edit_insight_title = w.get("insight_title", "")
                self.edit_insight_description = w.get("insight_description", "")
                return

    def save_widget_edit(self):
        """Save edits to the widget being edited."""
        for i, w in enumerate(self.widgets):
            if w.get("id") == self.editing_widget_id:
                w["title"] = self.edit_title
                w["content"] = self.edit_content
                w["kpi_value"] = self.edit_kpi_value
                w["kpi_label"] = self.edit_kpi_label
                w["insight_title"] = self.edit_insight_title
                w["insight_description"] = self.edit_insight_description
                self.widgets[i] = w
                break
        self.editing_widget_id = ""

    def cancel_edit_widget(self):
        """Close edit dialog without saving."""
        self.editing_widget_id = ""

    @rx.var
    def is_editing(self) -> bool:
        return self.editing_widget_id != ""

    @rx.var
    def editing_widget_type(self) -> str:
        for w in self.widgets:
            if isinstance(w, dict) and w.get("id") == self.editing_widget_id:
                return w.get("widget_type", "")
        return ""

    def on_layout_change(self, new_layout: list[dict]):
        """Handle grid layout change from react-grid-layout."""
        self.layout = [
            {
                "i": item.get("i", ""),
                "x": int(item.get("x", 0)),
                "y": int(item.get("y", 0)),
                "w": int(item.get("w", 6)),
                "h": int(item.get("h", 3)),
            }
            for item in new_layout
            if item.get("i")
        ]

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

    @rx.event(background=True)
    async def add_from_current_chart(self):
        """Copy the current chart from ChartState into dashboard as a widget."""
        from biai.state.chart import ChartState

        async with self:
            chart = await self.get_state(ChartState)

        async with chart:
            show = chart.show_echarts
            title = chart.chart_title or "Chart"
            option = dict(chart.echarts_option) if chart.echarts_option else {}

        if not show:
            async with self:
                return rx.toast.error("No chart to add")

        async with self:
            self.add_chart_widget(title=title, echarts_option=option)
            return rx.toast.success(f"Widget '{title}' added to Dashboard Builder")

    # --- Persistence ---

    def save_dashboard(self):
        """Save current dashboard."""
        import json as _json

        name = self.save_name or self.dashboard_name
        # Convert Reflex state proxy objects to plain Python via JSON round-trip
        widgets = _json.loads(_json.dumps(list(self.widgets)))
        layout = _json.loads(_json.dumps(list(self.layout)))
        DashboardStorage.save(name, widgets, layout)
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
        else:
            return rx.toast.error(f"Failed to load dashboard '{name}'")

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

    # --- Default Dashboard ---

    @rx.var
    def has_default_dashboard(self) -> bool:
        return self.default_dashboard_name != "" and len(self.default_widgets) > 0

    def set_as_default(self):
        """Set current dashboard as the default (shown on main page)."""
        import json as _json

        name = self.dashboard_name
        if not self.widgets:
            return rx.toast.error("Dashboard is empty — nothing to set as default")

        # Save first if not yet saved
        widgets = _json.loads(_json.dumps(list(self.widgets)))
        layout = _json.loads(_json.dumps(list(self.layout)))
        DashboardStorage.save(name, widgets, layout)
        DashboardStorage.set_default(name)

        self.default_dashboard_name = name
        self.default_widgets = widgets
        self.default_layout = layout
        self.saved_dashboards = DashboardStorage.list_dashboards()
        return rx.toast.success(f"'{name}' set as default dashboard")

    def clear_default(self):
        """Remove the default dashboard."""
        DashboardStorage.set_default("")
        self.default_dashboard_name = ""
        self.default_widgets = []
        self.default_layout = []
        return rx.toast.info("Default dashboard cleared")

    def load_default_on_init(self):
        """Load the default dashboard on main page init."""
        name = DashboardStorage.get_default()
        if not name:
            self.default_dashboard_name = ""
            self.default_widgets = []
            self.default_layout = []
            return
        data = DashboardStorage.load(name)
        if data and data.get("widgets"):
            self.default_dashboard_name = data.get("name", name)
            self.default_widgets = data.get("widgets", [])
            self.default_layout = data.get("layout", [])
        else:
            self.default_dashboard_name = ""
            self.default_widgets = []
            self.default_layout = []

"""Dashboard Builder page component — full-width grid with widget palette."""

import reflex as rx

from biai.state.dashboard import DashboardState
from biai.components.dashboard_builder.grid_layout import dashboard_grid
from biai.components.dashboard_builder.widget import dashboard_widget


def dashboard_builder_page() -> rx.Component:
    """Full dashboard builder view."""
    return rx.vstack(
        # Top toolbar
        _toolbar(),

        # Main content
        rx.hstack(
            # Widget palette (collapsible sidebar)
            rx.cond(
                DashboardState.show_widget_palette,
                _widget_palette(),
            ),

            # Grid area
            rx.box(
                rx.cond(
                    DashboardState.has_widgets,
                    rx.box(
                        dashboard_grid(
                            rx.foreach(
                                DashboardState.widgets,
                                dashboard_widget,
                            ),
                            layout=DashboardState.layout,
                            cols=12,
                            row_height=80,
                            is_draggable=DashboardState.is_edit_mode,
                            is_resizable=DashboardState.is_edit_mode,
                            on_layout_change=DashboardState.on_layout_change,
                        ),
                        width="100%",
                        min_height="calc(100vh - 60px)",
                    ),
                    _empty_grid(),
                ),
                flex="1",
                overflow_y="auto",
                padding="16px",
            ),
            width="100%",
            flex="1",
            spacing="0",
        ),

        # Save dialog
        rx.cond(
            DashboardState.show_save_dialog,
            _save_dialog(),
        ),

        width="100%",
        height="100vh",
        spacing="0",
        bg="var(--color-background)",
    )


def _toolbar() -> rx.Component:
    """Dashboard toolbar with actions."""
    return rx.hstack(
        rx.hstack(
            rx.icon("layout-dashboard", size=20, color="var(--accent-9)"),
            rx.text(DashboardState.dashboard_name, size="4", weight="bold"),
            spacing="2",
            align="center",
        ),
        rx.spacer(),
        # Widget palette toggle
        rx.tooltip(
            rx.button(
                rx.icon("plus", size=14),
                "Add Widget",
                variant=rx.cond(DashboardState.show_widget_palette, "soft", "outline"),
                size="1",
                on_click=DashboardState.toggle_widget_palette,
            ),
            content="Toggle widget palette",
        ),
        # Edit mode toggle
        rx.tooltip(
            rx.button(
                rx.icon(
                    rx.cond(DashboardState.is_edit_mode, "lock-open", "lock"),
                    size=14,
                ),
                rx.cond(DashboardState.is_edit_mode, "Editing", "Locked"),
                variant="outline",
                size="1",
                on_click=DashboardState.toggle_edit_mode,
            ),
            content="Toggle edit/lock mode",
        ),
        # Save
        rx.button(
            rx.icon("save", size=14),
            "Save",
            variant="outline",
            size="1",
            on_click=DashboardState.set_show_save_dialog(True),
        ),
        # Load saved
        rx.menu.root(
            rx.menu.trigger(
                rx.button(
                    rx.icon("folder-open", size=14),
                    "Load",
                    variant="outline",
                    size="1",
                    on_click=DashboardState.refresh_saved_list,
                ),
            ),
            rx.menu.content(
                rx.cond(
                    DashboardState.saved_dashboards.length() > 0,
                    rx.foreach(
                        DashboardState.saved_dashboards,
                        lambda d: rx.menu.item(
                            d["name"],
                            on_click=DashboardState.load_dashboard(d["file"]),
                        ),
                    ),
                    rx.menu.item("No saved dashboards", disabled=True),
                ),
            ),
        ),
        # Back to main
        rx.link(
            rx.button(
                rx.icon("arrow-left", size=14),
                "Back",
                variant="ghost",
                size="1",
            ),
            href="/",
        ),
        width="100%",
        align="center",
        padding="8px 16px",
        border_bottom="1px solid var(--gray-a5)",
        bg="var(--color-panel)",
        spacing="2",
    )


def _widget_palette() -> rx.Component:
    """Sidebar palette for adding widgets."""
    return rx.vstack(
        rx.text("Add Widget", size="2", weight="bold"),
        _palette_item("chart", "bar-chart-3", "Chart", "Add a visualization"),
        _palette_item("kpi", "hash", "KPI", "Big number metric"),
        _palette_item("table", "table-2", "Table", "Data table view"),
        _palette_item("text", "type", "Text", "Notes or description"),
        _palette_item("insight", "lightbulb", "Insight", "AI-generated insight"),
        width="200px",
        min_width="200px",
        padding="12px",
        border_right="1px solid var(--gray-a5)",
        spacing="2",
        height="calc(100vh - 60px)",
        bg="var(--color-panel)",
    )


def _palette_item(widget_type: str, icon_name: str, label: str, desc: str) -> rx.Component:
    """Single item in widget palette."""
    return rx.button(
        rx.hstack(
            rx.icon(icon_name, size=16, color="var(--accent-9)"),
            rx.vstack(
                rx.text(label, size="2", weight="medium"),
                rx.text(desc, size="1", color="var(--gray-9)"),
                spacing="0",
            ),
            spacing="2",
            align="center",
        ),
        variant="ghost",
        width="100%",
        on_click=DashboardState.add_widget(widget_type),
    )


def _empty_grid() -> rx.Component:
    """Empty dashboard state."""
    return rx.center(
        rx.vstack(
            rx.icon("layout-dashboard", size=48, color="var(--gray-8)", opacity=0.4),
            rx.text("Empty Dashboard", size="3", color="var(--gray-10)"),
            rx.text(
                "Click 'Add Widget' to start building your dashboard",
                size="2",
                color="var(--gray-9)",
            ),
            rx.button(
                rx.icon("plus", size=14),
                "Add First Widget",
                on_click=DashboardState.toggle_widget_palette,
                margin_top="8px",
            ),
            align="center",
            spacing="2",
        ),
        width="100%",
        height="calc(100vh - 60px)",
    )


def _save_dialog() -> rx.Component:
    """Save dashboard dialog."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Save Dashboard"),
            rx.vstack(
                rx.text("Dashboard name:", size="2"),
                rx.input(
                    placeholder="My Dashboard",
                    value=DashboardState.save_name,
                    on_change=DashboardState.set_save_name,
                    width="100%",
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button("Cancel", variant="outline", size="2"),
                    ),
                    rx.dialog.close(
                        rx.button(
                            "Save",
                            size="2",
                            on_click=DashboardState.save_dashboard,
                        ),
                    ),
                    spacing="2",
                    justify="end",
                    width="100%",
                ),
                spacing="3",
            ),
        ),
        open=DashboardState.show_save_dialog,
        on_open_change=DashboardState.set_show_save_dialog,
    )

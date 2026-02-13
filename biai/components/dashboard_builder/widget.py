"""Dashboard widget component — wraps chart/table/KPI/text content."""

import reflex as rx

from biai.components.echarts.wrapper import echarts_component
from biai.state.dashboard import DashboardState


def dashboard_widget(widget: dict) -> rx.Component:
    """Render a single dashboard widget inside the grid."""
    return rx.box(
        rx.card(
            rx.vstack(
                # Header with drag handle
                rx.hstack(
                    rx.box(
                        rx.icon("grip-vertical", size=14, color="var(--gray-8)"),
                        cursor="grab",
                        class_name="widget-drag-handle",
                        padding="2px",
                    ),
                    rx.text(
                        widget["title"],
                        size="2",
                        weight="bold",
                        truncate=True,
                    ),
                    rx.spacer(),
                    rx.badge(widget["widget_type"], size="1", variant="surface"),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("settings", size=12),
                            variant="ghost",
                            size="1",
                            on_click=DashboardState.start_edit_widget(widget["id"]),
                        ),
                        content="Edit widget",
                    ),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("x", size=12),
                            variant="ghost",
                            size="1",
                            color_scheme="red",
                            on_click=DashboardState.remove_widget(widget["id"]),
                        ),
                        content="Remove widget",
                    ),
                    width="100%",
                    align="center",
                    spacing="2",
                ),
                # Content based on type
                rx.cond(
                    widget["widget_type"] == "chart",
                    rx.cond(
                        widget.contains("echarts_option"),
                        rx.box(
                            echarts_component(
                                option=widget["echarts_option"],
                                not_merge=True,
                            ),
                            width="100%",
                            flex="1",
                            min_height="200px",
                        ),
                        rx.center(
                            rx.text("No chart data", size="2", color="var(--gray-9)"),
                            flex="1",
                        ),
                    ),
                    rx.cond(
                        widget["widget_type"] == "kpi",
                        _kpi_widget(widget),
                        rx.cond(
                            widget["widget_type"] == "text",
                            rx.box(
                                rx.markdown(widget.get("content", ""), size="2"),
                                padding="8px",
                                flex="1",
                            ),
                            rx.cond(
                                widget["widget_type"] == "insight",
                                _insight_widget(widget),
                                # Default: table or unknown
                                rx.center(
                                    rx.vstack(
                                        rx.text(widget["widget_type"], size="2", weight="medium"),
                                        rx.text(
                                            widget.get("subtitle", ""),
                                            size="1",
                                            color="var(--gray-9)",
                                        ),
                                        align="center",
                                    ),
                                    flex="1",
                                ),
                            ),
                        ),
                    ),
                ),
                width="100%",
                height="100%",
                spacing="2",
            ),
            size="1",
            width="100%",
            height="100%",
        ),
        key=widget["id"],
        width="100%",
        height="100%",
    )


def _kpi_widget(widget: dict) -> rx.Component:
    """KPI widget — large number + label."""
    return rx.center(
        rx.vstack(
            rx.text(
                widget.get("kpi_value", "—"),
                size="7",
                weight="bold",
                color="var(--accent-11)",
            ),
            rx.text(
                widget.get("kpi_label", ""),
                size="2",
                color="var(--gray-11)",
            ),
            align="center",
            spacing="1",
        ),
        flex="1",
    )


def _insight_widget(widget: dict) -> rx.Component:
    """Insight widget — icon + text."""
    return rx.vstack(
        rx.hstack(
            rx.icon("lightbulb", size=16, color="var(--amber-9)"),
            rx.text(widget.get("insight_title", ""), size="2", weight="bold"),
            spacing="2",
            align="center",
        ),
        rx.text(
            widget.get("insight_description", ""),
            size="1",
            color="var(--gray-11)",
        ),
        spacing="2",
        padding="8px",
        flex="1",
    )

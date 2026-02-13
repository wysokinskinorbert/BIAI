"""Dashboard panel with chart, data table, process flow, ERD, and SQL viewer."""

import reflex as rx

from biai.state.query import QueryState
from biai.state.chart import ChartState
from biai.state.chat import ChatState
from biai.state.process import ProcessState
from biai.state.process_map import ProcessMapState
from biai.state.schema import SchemaState
from biai.components.chart_card import chart_card
from biai.components.data_table import data_table
from biai.components.kpi_card import kpi_card
from biai.components.sql_viewer import sql_viewer
from biai.components.react_flow.process_flow import process_flow_card
from biai.components.react_flow.process_comparison import process_comparison_card
from biai.components.process_map_card import process_map_card
from biai.components.erd_diagram import erd_card
from biai.state.pinned import PinnedState
from biai.components.echarts.wrapper import echarts_component


def dashboard_panel() -> rx.Component:
    """Dashboard panel: chart + table + SQL viewer."""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.icon("layout-dashboard", size=20, color="var(--accent-9)"),
            rx.text("Dashboard", size="4", weight="bold"),
            rx.spacer(),
            # Pin current result
            rx.cond(
                QueryState.has_data,
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("pin", size=14),
                        variant="outline",
                        size="1",
                        on_click=PinnedState.pin_current_result,
                        aria_label="Pin result",
                    ),
                    content="Pin this result to dashboard",
                ),
            ),
            # Show pinned count badge
            rx.cond(
                PinnedState.has_pinned,
                rx.tooltip(
                    rx.button(
                        rx.icon("layout-grid", size=14),
                        PinnedState.pinned_count.to(str),
                        variant="outline",
                        size="1",
                        on_click=PinnedState.toggle_pinned,
                    ),
                    content="Show/hide pinned results",
                ),
            ),
            # Export CSV button
            rx.cond(
                QueryState.has_data,
                rx.tooltip(
                    rx.button(
                        rx.icon("download", size=14),
                        "CSV",
                        variant="outline",
                        size="1",
                        on_click=rx.download(
                            data=QueryState.csv_data,
                            filename="biai_export.csv",
                        ),
                        aria_label="Export CSV",
                    ),
                    content="Export data as CSV",
                ),
            ),
            width="100%",
            align="center",
            padding="12px 16px",
            border_bottom="1px solid var(--gray-a5)",
        ),

        # Content area
        rx.box(
            rx.cond(
                QueryState.has_data,
                # Has data: show pinned items + chart + table + SQL
                rx.vstack(
                    # Pinned results grid
                    rx.cond(
                        PinnedState.has_pinned & PinnedState.show_pinned,
                        rx.vstack(
                            rx.hstack(
                                rx.icon("layout-grid", size=14, color="var(--accent-9)"),
                                rx.text("Pinned Results", size="2", weight="medium"),
                                rx.spacer(),
                                rx.button(
                                    "Clear All",
                                    variant="ghost",
                                    size="1",
                                    color_scheme="red",
                                    on_click=PinnedState.clear_all_pinned,
                                ),
                                width="100%",
                                align="center",
                            ),
                            rx.box(
                                rx.foreach(
                                    PinnedState.pinned_items,
                                    _pinned_card,
                                ),
                                width="100%",
                                display="grid",
                                grid_template_columns="repeat(auto-fit, minmax(350px, 1fr))",
                                gap="12px",
                            ),
                            width="100%",
                            spacing="2",
                            padding_bottom="8px",
                            border_bottom="1px solid var(--gray-a4)",
                        ),
                    ),

                    # KPI card for single-row results
                    rx.box(
                        kpi_card(),
                        display=rx.cond(QueryState.is_kpi, "block", "none"),
                        width="100%",
                    ),

                    # Chart card (always rendered, visibility via CSS to avoid hooks warning)
                    rx.box(
                        chart_card(),
                        display=rx.cond(ChartState.has_chart, "block", "none"),
                        width="100%",
                    ),

                    # Process map card (discovery)
                    rx.box(
                        process_map_card(),
                        display=rx.cond(
                            ProcessMapState.show_map_or_discovering,
                            "block",
                            "none",
                        ),
                        width="100%",
                    ),

                    # Process flow card (visibility via CSS)
                    rx.box(
                        process_flow_card(),
                        display=rx.cond(ProcessState.show_process, "block", "none"),
                        width="100%",
                    ),

                    # Process comparison card (side-by-side)
                    rx.box(
                        process_comparison_card(),
                        display=rx.cond(ProcessState.show_comparison, "block", "none"),
                        width="100%",
                    ),

                    # Data table
                    data_table(),

                    # SQL viewer (always rendered, visibility via CSS)
                    rx.box(
                        sql_viewer(),
                        display=rx.cond(QueryState.current_sql != "", "block", "none"),
                        width="100%",
                    ),

                    width="100%",
                    spacing="4",
                    padding="16px",
                ),

                # No data: loading skeleton, ERD, or empty state
                rx.cond(
                    ChatState.is_processing,
                    _loading_skeleton(),
                    rx.cond(
                        SchemaState.has_erd,
                        rx.vstack(
                            erd_card(),
                            width="100%",
                            spacing="4",
                            padding="16px",
                        ),
                        _empty_dashboard(),
                    ),
                ),
            ),
            flex="1",
            overflow_y="auto",
            width="100%",
            tab_index=-1,
        ),

        width="100%",
        height="100%",
        spacing="0",
    )


def _pinned_card(item: rx.Var[dict]) -> rx.Component:
    """Render a pinned result card (mini chart + summary)."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.text(item["title"], size="1", weight="medium", truncate=True),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("x", size=10),
                    variant="ghost",
                    size="1",
                    on_click=PinnedState.unpin_item(item["id"]),
                ),
                width="100%",
                align="center",
            ),
            # Mini chart (ECharts only for pinned)
            rx.cond(
                item["engine"] == "echarts",
                rx.box(
                    echarts_component(
                        option=item["echarts_option"],
                        not_merge=True,
                    ),
                    width="100%",
                    height="180px",
                ),
                rx.text(
                    item["row_count"].to(str) + " rows",
                    size="1",
                    color="var(--gray-9)",
                ),
            ),
            width="100%",
            spacing="2",
        ),
        size="1",
    )


def _loading_skeleton() -> rx.Component:
    """Skeleton loader shown while AI processes a query."""
    return rx.vstack(
        # Chart skeleton
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.skeleton(width="16px", height="16px"),
                    rx.skeleton(width="200px", height="18px"),
                    rx.spacer(),
                    rx.skeleton(width="60px", height="20px"),
                    width="100%",
                    align="center",
                ),
                rx.skeleton(width="100%", height="280px"),
                width="100%",
                spacing="3",
            ),
            width="100%",
        ),
        # Table skeleton
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.skeleton(width="16px", height="16px"),
                    rx.skeleton(width="80px", height="18px"),
                    rx.spacer(),
                    rx.skeleton(width="60px", height="20px"),
                    rx.skeleton(width="50px", height="20px"),
                    width="100%",
                    align="center",
                ),
                rx.skeleton(width="100%", height="120px"),
                width="100%",
                spacing="3",
            ),
            width="100%",
        ),
        # SQL skeleton
        rx.card(
            rx.hstack(
                rx.skeleton(width="16px", height="16px"),
                rx.skeleton(width="120px", height="18px"),
                rx.spacer(),
                rx.skeleton(width="40px", height="20px"),
                width="100%",
                align="center",
            ),
            width="100%",
        ),
        width="100%",
        spacing="4",
        padding="16px",
    )


def _empty_dashboard() -> rx.Component:
    """Empty dashboard state."""
    return rx.center(
        rx.vstack(
            rx.icon("bar-chart-3", size=48, color="var(--gray-8)", opacity=0.4),
            rx.text(
                "Your charts and data will appear here",
                size="3",
                color="var(--gray-10)",
            ),
            rx.text(
                "Ask a question in the chat to get started",
                size="2",
                color="var(--gray-9)",
            ),
            align="center",
            spacing="2",
        ),
        width="100%",
        height="100%",
    )

"""Dashboard panel with chart, data table, process flow, ERD, and SQL viewer."""

import reflex as rx

from biai.state.query import QueryState
from biai.state.chart import ChartState
from biai.state.process import ProcessState
from biai.state.process_map import ProcessMapState
from biai.state.schema import SchemaState
from biai.components.chart_card import chart_card
from biai.components.data_table import data_table
from biai.components.sql_viewer import sql_viewer
from biai.components.react_flow.process_flow import process_flow_card
from biai.components.react_flow.process_comparison import process_comparison_card
from biai.components.process_map_card import process_map_card
from biai.components.erd_diagram import erd_card


def dashboard_panel() -> rx.Component:
    """Dashboard panel: chart + table + SQL viewer."""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.icon("layout-dashboard", size=20, color="var(--accent-9)"),
            rx.text("Dashboard", size="4", weight="bold"),
            rx.spacer(),
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
                # Has data: show chart + table + SQL
                rx.vstack(
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

                # No data: show ERD if schema available, else empty state
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
            flex="1",
            overflow_y="auto",
            width="100%",
            tab_index=-1,
        ),

        width="100%",
        height="100%",
        spacing="0",
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

"""Dashboard panel with chart, data table, and SQL viewer."""

import reflex as rx

from biai.state.query import QueryState
from biai.state.chart import ChartState
from biai.components.chart_card import chart_card
from biai.components.data_table import data_table
from biai.components.sql_viewer import sql_viewer


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
                rx.button(
                    rx.icon("download", size=14),
                    "CSV",
                    variant="outline",
                    size="1",
                    on_click=QueryState.prepare_csv_export,
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
                    # Chart card
                    rx.cond(
                        ChartState.show_echarts | ChartState.show_plotly,
                        chart_card(),
                    ),

                    # Data table
                    data_table(),

                    # SQL viewer
                    rx.cond(
                        QueryState.current_sql != "",
                        sql_viewer(),
                    ),

                    width="100%",
                    spacing="4",
                    padding="16px",
                ),

                # No data: empty state
                _empty_dashboard(),
            ),
            flex="1",
            overflow_y="auto",
            width="100%",
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

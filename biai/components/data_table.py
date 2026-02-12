"""Data table component for query results."""

import reflex as rx

from biai.state.query import QueryState


def data_table() -> rx.Component:
    """Data table with query results."""
    return rx.card(
        rx.vstack(
            # Header
            rx.hstack(
                rx.icon("table-2", size=16, color="green.9"),
                rx.text("Results", size="3", weight="medium"),
                rx.spacer(),
                rx.badge(
                    QueryState.row_count.to(str) + " rows",
                    variant="soft",
                    size="1",
                ),
                rx.badge(
                    QueryState.execution_time_display,
                    variant="soft",
                    size="1",
                    color_scheme="blue",
                ),
                rx.cond(
                    QueryState.is_truncated,
                    rx.badge("truncated", variant="soft", size="1", color_scheme="orange"),
                ),
                width="100%",
                align="center",
            ),

            # Table
            rx.cond(
                QueryState.has_data,
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.foreach(
                                    QueryState.columns,
                                    lambda col: rx.table.column_header_cell(
                                        rx.text(col, size="1", weight="bold"),
                                    ),
                                ),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(
                                QueryState.display_rows,
                                _table_row,
                            ),
                        ),
                        width="100%",
                        size="1",
                    ),
                    width="100%",
                    overflow_x="auto",
                    max_height="300px",
                    overflow_y="auto",
                ),
                rx.text("No data", size="2", color="var(--gray-10)"),
            ),

            width="100%",
            spacing="3",
        ),
        width="100%",
    )


def _table_row(row: list[str]) -> rx.Component:
    """Render a single table row."""
    return rx.table.row(
        rx.foreach(
            row,
            lambda cell: rx.table.cell(
                rx.text(cell, size="1"),
            ),
        ),
    )

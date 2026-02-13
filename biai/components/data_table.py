"""Data table component for query results with pagination and sorting."""

import reflex as rx

from biai.state.query import QueryState


def data_table() -> rx.Component:
    """Data table with query results, pagination, and column sorting."""
    return rx.card(
        rx.vstack(
            # Header
            rx.hstack(
                rx.icon("table-2", size=16, color="var(--accent-9)"),
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
                rx.vstack(
                    rx.box(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.foreach(
                                        QueryState.columns,
                                        _sortable_header,
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
                        max_height="350px",
                        overflow_y="auto",
                    ),
                    # Pagination controls
                    rx.cond(
                        QueryState.has_pagination,
                        rx.hstack(
                            rx.icon_button(
                                rx.icon("chevron-left", size=14),
                                variant="ghost",
                                size="1",
                                on_click=QueryState.table_prev_page,
                                disabled=~QueryState.can_prev_page,
                            ),
                            rx.text(
                                QueryState.table_page_display,
                                size="1",
                                color="var(--gray-10)",
                            ),
                            rx.icon_button(
                                rx.icon("chevron-right", size=14),
                                variant="ghost",
                                size="1",
                                on_click=QueryState.table_next_page,
                                disabled=~QueryState.can_next_page,
                            ),
                            justify="center",
                            align="center",
                            spacing="2",
                            width="100%",
                        ),
                    ),
                    width="100%",
                    spacing="2",
                ),
                rx.text("No data", size="2", color="var(--gray-10)"),
            ),

            width="100%",
            spacing="3",
        ),
        width="100%",
    )


def _sortable_header(col: rx.Var[str]) -> rx.Component:
    """Render a sortable column header."""
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(col, size="1", weight="bold"),
            rx.cond(
                QueryState.sort_column == col,
                rx.text(QueryState.sort_indicator, size="1", color="var(--accent-9)"),
            ),
            spacing="1",
            align="center",
            cursor="pointer",
            on_click=QueryState.sort_by(col),
            _hover={"opacity": "0.8"},
        ),
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

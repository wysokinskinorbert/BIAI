"""Schema explorer tree component."""

import reflex as rx

from biai.state.schema import SchemaState
from biai.state.database import DBState


def schema_explorer() -> rx.Component:
    """Database schema explorer with search and tree view."""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.text("Schema Explorer", size="3", weight="bold"),
            rx.spacer(),
            rx.tooltip(
                rx.icon_button(
                    rx.icon("refresh-cw", size=14),
                    on_click=SchemaState.refresh_schema,
                    loading=SchemaState.is_loading,
                    variant="ghost",
                    size="1",
                    aria_label="Refresh schema",
                ),
                content="Refresh schema",
            ),
            width="100%",
            align="center",
        ),

        # Not connected warning
        rx.callout(
            "Connect to a database first",
            icon="info",
            color_scheme="blue",
            size="1",
            width="100%",
            display=rx.cond(~DBState.is_connected, "flex", "none"),
        ),

        # Search
        rx.cond(
            DBState.is_connected,
            rx.input(
                placeholder="Search tables...",
                value=SchemaState.search_query,
                on_change=SchemaState.set_search_query,
                size="2",
                width="100%",
            ),
        ),

        # Error (CSS display to avoid ghost a11y node)
        rx.callout(
            SchemaState.schema_error,
            icon="triangle-alert",
            color_scheme="red",
            size="1",
            width="100%",
            display=rx.cond(SchemaState.schema_error != "", "flex", "none"),
        ),

        # Table list (flat - no nested foreach)
        rx.cond(
            DBState.is_connected,
            rx.box(
                rx.foreach(
                    SchemaState.filtered_tables,
                    _table_item,
                ),
                width="100%",
                overflow_y="auto",
                max_height="35vh",
            ),
        ),

        # Selected table columns (separate section, not nested)
        rx.cond(
            SchemaState.selected_table != "",
            rx.vstack(
                rx.separator(),
                rx.hstack(
                    rx.icon("table-2", size=14, color="var(--accent-9)"),
                    rx.text(SchemaState.selected_table, size="2", weight="bold"),
                    align="center",
                    spacing="2",
                ),
                rx.box(
                    rx.foreach(
                        SchemaState.selected_columns,
                        _column_item,
                    ),
                    width="100%",
                    overflow_y="auto",
                    max_height="25vh",
                ),
                width="100%",
                spacing="2",
            ),
        ),

        width="100%",
        spacing="3",
        padding="8px",
    )


def _table_item(table: dict) -> rx.Component:
    """Single table item in the schema explorer."""
    return rx.hstack(
        rx.icon("table-2", size=14, color="var(--accent-9)"),
        rx.text(table["name"], size="2", weight="medium"),
        rx.spacer(),
        rx.badge(table["col_count"].to(str), size="1", variant="soft"),
        width="100%",
        align="center",
        cursor="pointer",
        padding="6px 8px",
        border_radius="6px",
        _hover={"bg": "var(--gray-a3)"},
        on_click=SchemaState.select_table(table["name"]),
    )


def _column_item(col: dict) -> rx.Component:
    """Single column in the schema explorer."""
    return rx.hstack(
        rx.icon("columns-3", size=12, color="var(--gray-9)"),
        rx.text(col["name"], size="1", weight="medium"),
        rx.text(col["data_type"], size="1", color="var(--gray-11)"),
        spacing="2",
        align="center",
        padding="2px 4px",
    )

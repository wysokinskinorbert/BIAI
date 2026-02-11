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
            rx.icon_button(
                rx.icon("refresh-cw", size=14),
                on_click=SchemaState.refresh_schema,
                loading=SchemaState.is_loading,
                variant="ghost",
                size="1",
            ),
            width="100%",
            align="center",
        ),

        # Not connected warning
        rx.cond(
            ~DBState.is_connected,
            rx.callout(
                "Connect to a database first",
                icon="info",
                size="1",
                width="100%",
            ),
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

        # Error
        rx.cond(
            SchemaState.schema_error != "",
            rx.text(SchemaState.schema_error, size="1", color="red.11"),
        ),

        # Table list
        rx.cond(
            DBState.is_connected,
            rx.box(
                rx.foreach(
                    SchemaState.filtered_tables,
                    _table_item,
                ),
                width="100%",
                overflow_y="auto",
                max_height="60vh",
            ),
        ),

        width="100%",
        spacing="3",
        padding="8px",
    )


def _table_item(table: dict) -> rx.Component:
    """Single table item in the schema explorer."""
    return rx.box(
        rx.hstack(
            rx.icon("table-2", size=14, color="var(--accent-9)"),
            rx.text(table["name"], size="2", weight="medium"),
            rx.spacer(),
            rx.badge(table["col_count"].to(str), size="1", variant="soft"),
            width="100%",
            align="center",
            cursor="pointer",
            on_click=SchemaState.select_table(table["name"]),
        ),
        # Show columns when selected
        rx.cond(
            SchemaState.selected_table == table["name"],
            rx.box(
                rx.foreach(
                    table["columns"],
                    _column_item,
                ),
                padding_left="24px",
                padding_top="4px",
            ),
        ),
        padding="6px 8px",
        border_radius="6px",
        _hover={"bg": "var(--gray-a3)"},
        width="100%",
    )


def _column_item(col: dict) -> rx.Component:
    """Single column in the schema explorer."""
    return rx.hstack(
        rx.cond(
            col["is_pk"],
            rx.icon("key", size=12, color="yellow.9"),
            rx.cond(
                col["is_fk"],
                rx.icon("link", size=12, color="blue.9"),
                rx.icon("columns-3", size=12, color="var(--gray-9)"),
            ),
        ),
        rx.text(col["name"], size="1"),
        rx.text(col["data_type"], size="1", color="var(--gray-11)"),
        spacing="2",
        align="center",
        padding="2px 0",
    )

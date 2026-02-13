"""Data Explorer — interactive schema browser with profiling + glossary."""

import reflex as rx

from biai.state.schema import SchemaState
from biai.state.database import DBState




def data_explorer() -> rx.Component:
    """Data Explorer panel: table tree + profiles + glossary."""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.text("Data Explorer", size="3", weight="bold"),
            rx.spacer(),
            # Profiling button
            rx.tooltip(
                rx.icon_button(
                    rx.icon("scan-search", size=14),
                    on_click=SchemaState.run_profiling,
                    loading=SchemaState.is_profiling,
                    variant="ghost",
                    size="1",
                    aria_label="Profile tables",
                ),
                content="Auto-profile all tables",
            ),
            # Glossary button
            rx.tooltip(
                rx.icon_button(
                    rx.icon("book-open", size=14),
                    on_click=SchemaState.generate_glossary,
                    loading=SchemaState.is_generating_glossary,
                    variant="ghost",
                    size="1",
                    aria_label="Generate glossary",
                ),
                content="Generate AI business glossary",
            ),
            # Refresh schema
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

        # Profiling progress
        rx.cond(
            SchemaState.is_profiling,
            rx.hstack(
                rx.spinner(size="1"),
                rx.text(SchemaState.profiling_progress, size="1", color="var(--accent-11)"),
                spacing="2",
                align="center",
                width="100%",
            ),
        ),

        # Search
        rx.cond(
            DBState.is_connected,
            rx.input(
                placeholder="Search tables or descriptions...",
                value=SchemaState.search_query,
                on_change=SchemaState.set_search_query,
                size="2",
                width="100%",
            ),
        ),

        # Error
        rx.callout(
            SchemaState.schema_error,
            icon="triangle-alert",
            color_scheme="red",
            size="1",
            width="100%",
            display=rx.cond(SchemaState.schema_error != "", "flex", "none"),
        ),

        # Status badges
        rx.cond(
            DBState.is_connected & (SchemaState.has_profiles | SchemaState.has_glossary),
            rx.hstack(
                rx.cond(
                    SchemaState.has_profiles,
                    rx.badge(
                        rx.icon("scan-search", size=10),
                        "Profiled",
                        variant="surface",
                        size="1",
                        color_scheme="green",
                    ),
                ),
                rx.cond(
                    SchemaState.has_glossary,
                    rx.badge(
                        rx.icon("book-open", size=10),
                        "Glossary",
                        variant="surface",
                        size="1",
                        color_scheme="blue",
                    ),
                ),
                spacing="1",
            ),
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
                max_height="30vh",
            ),
        ),

        # Selected table detail
        rx.cond(
            SchemaState.selected_table != "",
            _table_detail_section(),
        ),

        width="100%",
        spacing="3",
        padding="8px",
    )


def _table_item(table: dict) -> rx.Component:
    """Single table item with glossary tooltip."""
    return rx.tooltip(
        rx.hstack(
            rx.icon("table-2", size=14, color="var(--accent-9)"),
            rx.vstack(
                rx.text(table["name"], size="2", weight="medium"),
                # Show business name from glossary if available
                rx.cond(
                    SchemaState.has_glossary,
                    rx.text(
                        SchemaState.glossary[table["name"]]["business_name"],
                        size="1",
                        color="var(--gray-9)",
                        display=rx.cond(
                            SchemaState.glossary.contains(table["name"]),
                            "block",
                            "none",
                        ),
                    ),
                ),
                spacing="0",
            ),
            rx.spacer(),
            rx.badge(table["col_count"].to(str), size="1", variant="soft"),
            width="100%",
            align="center",
            cursor="pointer",
            padding="6px 8px",
            border_radius="6px",
            bg=rx.cond(
                SchemaState.selected_table == table["name"],
                "var(--accent-a3)",
                "transparent",
            ),
            _hover={"bg": "var(--gray-a3)"},
            on_click=SchemaState.select_table(table["name"]),
        ),
        content=table["name"],
    )


def _table_detail_section() -> rx.Component:
    """Detailed view for selected table: profile + glossary + columns."""
    return rx.vstack(
        rx.separator(),

        # Table header
        rx.hstack(
            rx.icon("table-2", size=14, color="var(--accent-9)"),
            rx.vstack(
                rx.text(SchemaState.selected_table, size="2", weight="bold"),
                # Business name and description from glossary
                rx.cond(
                    SchemaState.selected_table_business_name != "",
                    rx.text(
                        SchemaState.selected_table_business_name,
                        size="1",
                        color="var(--accent-11)",
                        weight="medium",
                    ),
                ),
                spacing="0",
            ),
            rx.spacer(),
            # Row count badge
            rx.cond(
                SchemaState.selected_table_row_count != "",
                rx.badge(
                    SchemaState.selected_table_row_count + " rows",
                    size="1",
                    variant="surface",
                    color_scheme="blue",
                ),
            ),
            # Domain badge
            rx.cond(
                SchemaState.selected_table_domain != "",
                rx.badge(
                    SchemaState.selected_table_domain,
                    size="1",
                    variant="surface",
                ),
            ),
            align="center",
            spacing="2",
            width="100%",
        ),

        # Business description
        rx.cond(
            SchemaState.selected_table_description != "",
            rx.text(
                SchemaState.selected_table_description,
                size="1",
                color="var(--gray-11)",
                padding="4px 0",
            ),
        ),

        # Column profiles
        rx.cond(
            SchemaState.has_profiles,
            rx.box(
                rx.foreach(
                    SchemaState.selected_column_profiles,
                    _column_profile_card,
                ),
                width="100%",
                overflow_y="auto",
                max_height="35vh",
            ),
            # Fallback: simple column list
            rx.box(
                rx.foreach(
                    SchemaState.selected_columns,
                    _column_item_simple,
                ),
                width="100%",
                overflow_y="auto",
                max_height="25vh",
            ),
        ),

        width="100%",
        spacing="2",
    )


def _column_profile_card(profile: dict) -> rx.Component:
    """Rich column profile card with stats and semantic type.

    Profile is a flattened dict[str, str] — all values are strings,
    no nested dicts. Boolean flags use "1" for true, "" for false.
    """
    return rx.vstack(
        rx.hstack(
            rx.icon("columns-3", size=12, color="var(--accent-9)"),
            rx.text(profile["column_name"], size="1", weight="bold"),
            rx.text(profile["data_type"], size="1", color="var(--gray-9)"),
            rx.spacer(),
            rx.badge(profile["semantic_type"], size="1", variant="outline"),
            align="center",
            spacing="2",
            width="100%",
        ),
        # Stats row
        rx.hstack(
            rx.cond(
                profile["has_nulls"] != "",
                rx.text(
                    "null: " + profile["null_pct"] + "%",
                    size="1",
                    color=rx.cond(
                        profile["null_pct_high"] != "",
                        "var(--red-11)",
                        "var(--gray-9)",
                    ),
                ),
            ),
            rx.text(
                "distinct: " + profile["distinct_count"],
                size="1",
                color="var(--gray-9)",
            ),
            rx.cond(
                profile["has_mean"] != "",
                rx.text(
                    "avg: " + profile["mean"],
                    size="1",
                    color="var(--gray-9)",
                ),
            ),
            spacing="3",
            wrap="wrap",
        ),
        # Top values (pre-joined string)
        rx.cond(
            profile["show_top_values"] != "",
            rx.text(
                profile["top_values_str"],
                size="1",
                color="var(--gray-9)",
                padding="2px 0",
            ),
        ),
        # Anomalies (pre-joined string)
        rx.cond(
            profile["has_anomalies"] != "",
            rx.text(
                profile["anomalies_str"],
                size="1",
                color="var(--orange-11)",
            ),
        ),
        width="100%",
        spacing="1",
        padding="4px 0",
        border_bottom="1px solid var(--gray-a3)",
    )


def _column_item_simple(col: dict) -> rx.Component:
    """Simple column item (fallback when no profiles)."""
    return rx.hstack(
        rx.icon("columns-3", size=12, color="var(--gray-9)"),
        rx.text(col["name"], size="1", weight="medium"),
        rx.text(col["data_type"], size="1", color="var(--gray-11)"),
        spacing="2",
        align="center",
        padding="2px 4px",
    )

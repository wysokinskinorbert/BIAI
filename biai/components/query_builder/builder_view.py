"""Visual Query Builder view — React Flow canvas with block nodes."""

import reflex as rx

from biai.state.query_builder import QueryBuilderState
from biai.components.react_flow.wrapper import (
    react_flow,
    react_flow_background,
    react_flow_controls,
    react_flow_provider,
)


def query_builder_view() -> rx.Component:
    """Query Builder page view with React Flow canvas."""
    return rx.vstack(
        # Toolbar
        rx.hstack(
            rx.hstack(
                rx.icon("blocks", size=20, color="var(--accent-9)"),
                rx.text("Query Builder", size="4", weight="bold"),
                spacing="2",
                align="center",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("trash-2", size=14),
                "Clear All",
                variant="outline",
                size="1",
                color_scheme="red",
                on_click=QueryBuilderState.clear_all,
            ),
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
        ),

        # Main content: palette + canvas + config panel
        rx.hstack(
            # Block palette
            rx.vstack(
                rx.text("Blocks", size="2", weight="bold"),
                rx.foreach(
                    QueryBuilderState.block_types,
                    _block_palette_item,
                ),
                rx.separator(),
                rx.text("How to use", size="1", weight="medium", color="var(--gray-10)"),
                rx.text(
                    "1. Add blocks from palette\n"
                    "2. Drag to arrange\n"
                    "3. Connect: drag from bottom handle to top handle\n"
                    "4. Click block to configure",
                    size="1",
                    color="var(--gray-9)",
                    white_space="pre-line",
                ),
                width="180px",
                min_width="180px",
                padding="12px",
                border_right="1px solid var(--gray-a5)",
                spacing="2",
            ),

            # React Flow canvas
            rx.box(
                rx.cond(
                    QueryBuilderState.has_blocks,
                    rx.box(
                        react_flow_provider(
                            react_flow(
                                react_flow_background(
                                    variant="dots", gap=20,
                                    color=rx.color_mode_cond("#ccc", "#333"),
                                ),
                                react_flow_controls(
                                    show_zoom=True, show_fit_view=True,
                                    show_interactive=False,
                                ),
                                nodes=QueryBuilderState.flow_nodes,
                                edges=QueryBuilderState.flow_edges,
                                node_types=rx.Var("queryBuilderNodeTypes"),
                                fit_view=True,
                                color_mode=rx.color_mode_cond("light", "dark"),
                                nodes_draggable=True,
                                nodes_connectable=True,
                                elements_selectable=True,
                                on_node_click=QueryBuilderState.on_node_click,
                                on_connect=QueryBuilderState.on_connect,
                                on_nodes_change=QueryBuilderState.on_nodes_change,
                            ),
                        ),
                        width="100%",
                        height="100%",
                    ),
                    # Empty state
                    rx.center(
                        rx.vstack(
                            rx.icon("blocks", size=48, color="var(--gray-8)", opacity=0.4),
                            rx.text("Add blocks from the palette", size="2", color="var(--gray-9)"),
                            rx.text("Then connect them to build your query", size="1", color="var(--gray-8)"),
                            align="center",
                        ),
                        width="100%",
                        height="100%",
                    ),
                ),
                flex="1",
                height="calc(100vh - 60px - 200px)",
                min_height="350px",
            ),

            # Config panel (right sidebar, when block selected)
            rx.cond(
                QueryBuilderState.has_selected_block,
                _config_panel(),
            ),
            flex="1",
            spacing="0",
            width="100%",
        ),

        # Generated SQL preview + Run button (bottom)
        rx.cond(
            QueryBuilderState.has_sql,
            rx.vstack(
                rx.hstack(
                    rx.icon("code", size=14, color="var(--accent-9)"),
                    rx.text("Generated SQL", size="2", weight="bold"),
                    rx.spacer(),
                    rx.button(
                        rx.cond(
                            QueryBuilderState.is_previewing,
                            rx.fragment(
                                rx.spinner(size="1"),
                                rx.text("Running...", size="1"),
                            ),
                            rx.fragment(
                                rx.icon("play", size=14),
                                rx.text("Run Preview", size="1"),
                            ),
                        ),
                        variant="solid",
                        size="1",
                        on_click=QueryBuilderState.run_preview,
                        loading=QueryBuilderState.is_previewing,
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                rx.code_block(
                    QueryBuilderState.generated_sql,
                    language="sql",
                    show_line_numbers=True,
                    width="100%",
                ),
                # Preview error
                rx.cond(
                    QueryBuilderState.preview_error != "",
                    rx.callout(
                        QueryBuilderState.preview_error,
                        icon="triangle_alert",
                        color_scheme="red",
                        size="1",
                        width="100%",
                    ),
                ),
                # Preview results table
                rx.cond(
                    QueryBuilderState.has_preview,
                    rx.vstack(
                        rx.hstack(
                            rx.icon("table-2", size=14, color="var(--accent-9)"),
                            rx.text("Preview Results", size="2", weight="bold"),
                            rx.badge(
                                QueryBuilderState.preview_row_count.to(str) + " rows",
                                variant="soft",
                                size="1",
                            ),
                            spacing="2",
                            align="center",
                        ),
                        rx.scroll_area(
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.foreach(
                                            QueryBuilderState.preview_columns,
                                            lambda col: rx.table.column_header_cell(
                                                rx.text(col, size="1", weight="bold"),
                                            ),
                                        ),
                                    ),
                                ),
                                rx.table.body(
                                    rx.foreach(
                                        QueryBuilderState.preview_rows,
                                        lambda row: rx.table.row(
                                            rx.foreach(
                                                row,
                                                lambda cell: rx.table.cell(
                                                    rx.text(cell, size="1"),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                                size="1",
                                width="100%",
                            ),
                            max_height="200px",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                ),
                width="100%",
                spacing="2",
                padding="12px 16px",
                border_top="1px solid var(--gray-a5)",
                max_height="400px",
                overflow_y="auto",
            ),
        ),
        width="100%",
        height="100vh",
        spacing="0",
    )


def _block_palette_item(bt: dict) -> rx.Component:
    """Block type in palette."""
    return rx.button(
        rx.hstack(
            rx.icon(bt["icon"], size=14),
            rx.text(bt["label"], size="2"),
            spacing="2",
            align="center",
        ),
        variant="ghost",
        width="100%",
        on_click=QueryBuilderState.add_block(bt["type"]),
    )


def _config_panel() -> rx.Component:
    """Right sidebar for editing selected block's configuration."""
    cfg = QueryBuilderState.selected_block_config
    return rx.vstack(
        rx.hstack(
            rx.icon("settings", size=14, color="var(--accent-9)"),
            rx.text("Block Config", size="2", weight="bold"),
            rx.spacer(),
            rx.icon_button(
                rx.icon("x", size=12),
                variant="ghost",
                size="1",
                on_click=QueryBuilderState.set_selected_block_id(""),
            ),
            width="100%",
            align="center",
        ),
        rx.separator(),

        # Table config
        rx.cond(
            cfg["block_type"] == "table",
            rx.vstack(
                rx.text("Table Name:", size="1", weight="medium"),
                rx.input(
                    value=cfg["table_name"],
                    placeholder="e.g. orders",
                    on_change=QueryBuilderState.set_config_table_name,
                    size="1",
                    width="100%",
                ),
                rx.text("Alias:", size="1", weight="medium"),
                rx.input(
                    value=cfg["alias"],
                    placeholder="e.g. o",
                    on_change=QueryBuilderState.set_config_alias,
                    size="1",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
        ),

        # Filter config
        rx.cond(
            cfg["block_type"] == "filter",
            rx.vstack(
                rx.text("Column:", size="1", weight="medium"),
                rx.input(
                    value=cfg["column"],
                    placeholder="e.g. status",
                    on_change=QueryBuilderState.set_config_column,
                    size="1",
                    width="100%",
                ),
                rx.text("Operator:", size="1", weight="medium"),
                rx.select(
                    ["=", "!=", ">", "<", ">=", "<=", "LIKE", "ILIKE", "IN"],
                    value=cfg["operator"],
                    on_change=QueryBuilderState.set_config_operator,
                    size="1",
                    width="100%",
                ),
                rx.text("Value:", size="1", weight="medium"),
                rx.input(
                    value=cfg["value"],
                    placeholder="e.g. active",
                    on_change=QueryBuilderState.set_config_value,
                    size="1",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
        ),

        # Aggregate config
        rx.cond(
            cfg["block_type"] == "aggregate",
            rx.vstack(
                rx.text("Function:", size="1", weight="medium"),
                rx.select(
                    ["COUNT", "SUM", "AVG", "MIN", "MAX"],
                    value=cfg["function"],
                    on_change=QueryBuilderState.set_config_function,
                    size="1",
                    width="100%",
                ),
                rx.text("Column:", size="1", weight="medium"),
                rx.input(
                    value=cfg["column"],
                    placeholder="e.g. amount",
                    on_change=QueryBuilderState.set_config_column,
                    size="1",
                    width="100%",
                ),
                rx.text("Group By:", size="1", weight="medium"),
                rx.input(
                    value=cfg["group_by"],
                    placeholder="e.g. category",
                    on_change=QueryBuilderState.set_config_group_by,
                    size="1",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
        ),

        # Join config
        rx.cond(
            cfg["block_type"] == "join",
            rx.vstack(
                rx.text("Join Type:", size="1", weight="medium"),
                rx.select(
                    ["INNER", "LEFT", "RIGHT", "FULL"],
                    value=cfg["join_type"],
                    on_change=QueryBuilderState.set_config_join_type,
                    size="1",
                    width="100%",
                ),
                rx.text("Left Column:", size="1", weight="medium"),
                rx.input(
                    value=cfg["on_left"],
                    placeholder="e.g. orders.customer_id",
                    on_change=QueryBuilderState.set_config_on_left,
                    size="1",
                    width="100%",
                ),
                rx.text("Right Column:", size="1", weight="medium"),
                rx.input(
                    value=cfg["on_right"],
                    placeholder="e.g. customers.id",
                    on_change=QueryBuilderState.set_config_on_right,
                    size="1",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
        ),

        # Sort config
        rx.cond(
            cfg["block_type"] == "sort",
            rx.vstack(
                rx.text("Column:", size="1", weight="medium"),
                rx.input(
                    value=cfg["column"],
                    placeholder="e.g. created_at",
                    on_change=QueryBuilderState.set_config_column,
                    size="1",
                    width="100%",
                ),
                rx.text("Direction:", size="1", weight="medium"),
                rx.select(
                    ["ASC", "DESC"],
                    value=cfg["direction"],
                    on_change=QueryBuilderState.set_config_direction,
                    size="1",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
        ),

        # Limit config
        rx.cond(
            cfg["block_type"] == "limit",
            rx.vstack(
                rx.text("Row Count:", size="1", weight="medium"),
                rx.input(
                    value=cfg["count"],
                    placeholder="100",
                    on_change=QueryBuilderState.set_config_count,
                    size="1",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
        ),

        # Delete block button
        rx.separator(),
        rx.button(
            rx.icon("trash-2", size=12),
            "Remove Block",
            variant="outline",
            size="1",
            color_scheme="red",
            width="100%",
            on_click=QueryBuilderState.remove_block(
                QueryBuilderState.selected_block_id,
            ),
        ),

        width="220px",
        min_width="220px",
        padding="12px",
        border_left="1px solid var(--gray-a5)",
        spacing="2",
        overflow_y="auto",
        height="calc(100vh - 60px)",
    )

"""Visual Query Builder view — block-based SQL composition UI."""

import reflex as rx

from biai.state.query_builder import QueryBuilderState


def query_builder_view() -> rx.Component:
    """Query Builder page view."""
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

        # Main content
        rx.hstack(
            # Block palette
            rx.vstack(
                rx.text("Blocks", size="2", weight="bold"),
                rx.foreach(
                    QueryBuilderState.block_types,
                    _block_palette_item,
                ),
                width="180px",
                min_width="180px",
                padding="12px",
                border_right="1px solid var(--gray-a5)",
                spacing="2",
            ),

            # Canvas + SQL preview
            rx.vstack(
                # Blocks list
                rx.cond(
                    QueryBuilderState.has_blocks,
                    rx.vstack(
                        rx.foreach(
                            QueryBuilderState.blocks_display,
                            _block_card,
                        ),
                        width="100%",
                        spacing="2",
                        padding="16px",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon("blocks", size=48, color="var(--gray-8)", opacity=0.4),
                            rx.text("Add blocks from the palette", size="2", color="var(--gray-9)"),
                            align="center",
                        ),
                        flex="1",
                        width="100%",
                    ),
                ),

                # Generated SQL preview
                rx.cond(
                    QueryBuilderState.has_sql,
                    rx.vstack(
                        rx.hstack(
                            rx.icon("code", size=14, color="var(--accent-9)"),
                            rx.text("Generated SQL", size="2", weight="bold"),
                            spacing="2",
                            align="center",
                        ),
                        rx.code_block(
                            QueryBuilderState.generated_sql,
                            language="sql",
                            show_line_numbers=True,
                            width="100%",
                        ),
                        width="100%",
                        spacing="2",
                        padding="16px",
                        border_top="1px solid var(--gray-a5)",
                    ),
                ),
                flex="1",
                width="100%",
            ),
            flex="1",
            spacing="0",
            width="100%",
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


def _block_card(block: dict) -> rx.Component:
    """Render a block card with its configuration (flat dict[str, str])."""
    return rx.card(
        rx.hstack(
            rx.badge(block["type"], size="1", variant="surface"),
            rx.spacer(),
            rx.icon_button(
                rx.icon("x", size=10),
                variant="ghost",
                size="1",
                on_click=QueryBuilderState.remove_block(block["id"]),
            ),
            width="100%",
            align="center",
        ),
        rx.text(
            block["description"],
            size="1",
            color="var(--gray-11)",
        ),
        width="100%",
        size="1",
    )

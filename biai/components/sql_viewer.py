"""SQL viewer component with syntax display."""

import reflex as rx

from biai.state.query import QueryState


def sql_viewer() -> rx.Component:
    """SQL viewer with syntax highlighting style."""
    return rx.card(
        rx.vstack(
            # Header
            rx.hstack(
                rx.icon("code-2", size=16, color="var(--accent-9)"),
                rx.text("Generated SQL", size="3", weight="medium"),
                rx.spacer(),
                rx.cond(
                    QueryState.generation_attempts > 1,
                    rx.badge(
                        f"Attempt {QueryState.generation_attempts}",
                        variant="soft",
                        size="1",
                        color_scheme="orange",
                    ),
                ),
                rx.badge(
                    QueryState.sql_dialect,
                    variant="soft",
                    size="1",
                ),
                rx.icon_button(
                    rx.icon("copy", size=14),
                    variant="ghost",
                    size="1",
                    on_click=rx.set_clipboard(QueryState.current_sql),
                ),
                width="100%",
                align="center",
            ),

            # SQL code block
            rx.code_block(
                QueryState.current_sql,
                language="sql",
                show_line_numbers=True,
                width="100%",
            ),

            width="100%",
            spacing="3",
        ),
        width="100%",
    )

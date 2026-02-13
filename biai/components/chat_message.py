"""Chat message bubble component."""

import reflex as rx

from biai.state.chat import ChatState
from biai.state.saved_queries import SavedQueriesState


def chat_message(message: dict) -> rx.Component:
    """Render a single chat message bubble."""
    is_user = message["role"] == "user"

    return rx.box(
        rx.hstack(
            # AI Avatar (only for assistant)
            rx.cond(
                ~is_user,
                rx.avatar(
                    fallback="AI",
                    size="2",
                    color_scheme="violet",
                    variant="solid",
                ),
            ),

            # Message bubble
            rx.box(
                # Error indicator icon
                rx.cond(
                    message["is_error"],
                    rx.hstack(
                        rx.icon("alert-triangle", size=16, color="var(--red-9)"),
                        rx.text("Error", size="2", weight="bold", color="var(--red-11)"),
                        spacing="1",
                        align="center",
                        padding_bottom="4px",
                    ),
                ),
                # Content
                rx.cond(
                    message["is_streaming"],
                    rx.hstack(
                        rx.markdown(message["content"], size="2"),
                        rx.spinner(size="1"),
                        align="end",
                        spacing="2",
                    ),
                    rx.markdown(message["content"], size="2"),
                ),

                # SQL badge
                rx.cond(
                    message["has_table"],
                    rx.hstack(
                        rx.badge(
                            rx.icon("code", size=12),
                            "SQL",
                            variant="surface",
                            size="1",
                        ),
                        rx.badge(
                            rx.icon("table-2", size=12),
                            "Data",
                            variant="surface",
                            size="1",
                            color_scheme="green",
                        ),
                        rx.cond(
                            message["has_chart"],
                            rx.badge(
                                rx.icon("bar-chart-3", size=12),
                                "Chart",
                                variant="surface",
                                size="1",
                                color_scheme="blue",
                            ),
                        ),
                        rx.cond(
                            message["has_process"],
                            rx.badge(
                                rx.icon("workflow", size=12),
                                "Process",
                                variant="surface",
                                size="1",
                                color_scheme="purple",
                            ),
                        ),
                        # Save query button (only for completed AI responses with data)
                        rx.cond(
                            (message["question"] != "") & (~message["is_streaming"]),
                            rx.tooltip(
                                rx.icon_button(
                                    rx.icon("bookmark-plus", size=12),
                                    variant="ghost",
                                    size="1",
                                    on_click=SavedQueriesState.save_current_query(message["question"]),
                                    cursor="pointer",
                                ),
                                content="Save query",
                            ),
                        ),
                        spacing="1",
                        padding_top="8px",
                    ),
                ),

                # Retry button for errors
                rx.cond(
                    message["is_error"] & (message["question"] != ""),
                    rx.button(
                        rx.icon("refresh-cw", size=12),
                        "Retry",
                        variant="outline",
                        size="1",
                        color_scheme="red",
                        on_click=ChatState.run_suggested_query(message["question"]),
                        margin_top="8px",
                    ),
                ),

                padding="12px 16px",
                border_radius="12px",
                max_width="85%",
                bg=rx.cond(
                    is_user,
                    "var(--accent-3)",
                    rx.cond(
                        message["is_error"],
                        "var(--red-3)",
                        "var(--gray-a3)",
                    ),
                ),
            ),

            # User Avatar (only for user)
            rx.cond(
                is_user,
                rx.avatar(
                    fallback="U",
                    size="2",
                    color_scheme="gray",
                    variant="soft",
                ),
            ),

            width="100%",
            spacing="2",
            align="start",
            direction=rx.cond(is_user, "row-reverse", "row"),
        ),
        width="100%",
        padding="4px 0",
    )

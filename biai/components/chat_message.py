"""Chat message bubble component."""

import reflex as rx


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
                        spacing="1",
                        padding_top="8px",
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

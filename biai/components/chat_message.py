"""Chat message bubble component."""

import reflex as rx


def chat_message(message: dict) -> rx.Component:
    """Render a single chat message bubble."""
    is_user = message["role"] == "user"

    return rx.box(
        rx.hstack(
            # Avatar
            rx.cond(
                ~is_user,
                rx.avatar(
                    fallback="AI",
                    size="2",
                    color_scheme="violet",
                    variant="solid",
                ),
            ),
            rx.spacer() if is_user else rx.fragment(),

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

                # SQL badge (if available)
                rx.cond(
                    message["sql"] != None,  # noqa: E711
                    rx.badge(
                        rx.icon("code-2", size=12),
                        "SQL",
                        variant="surface",
                        size="1",
                        cursor="pointer",
                    ),
                ),

                # Data indicators
                rx.hstack(
                    rx.cond(
                        message["has_table"],
                        rx.badge(
                            rx.icon("table-2", size=12),
                            "Data",
                            variant="surface",
                            size="1",
                            color_scheme="green",
                        ),
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
                    spacing="1",
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

            rx.spacer() if not is_user else rx.fragment(),

            # User avatar
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
            justify=rx.cond(is_user, "end", "start"),
        ),
        width="100%",
        padding="4px 0",
    )

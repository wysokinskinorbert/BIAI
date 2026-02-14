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
                        rx.icon("triangle-alert", size=16, color="var(--red-9)"),
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

                # Multi-step analysis progress (per-message)
                rx.cond(
                    message["is_multi_step"],
                    _analysis_steps_section(message),
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

                # Insights section (per-message insights)
                rx.cond(
                    message["has_insights"],
                    rx.vstack(
                        rx.separator(),
                        rx.hstack(
                            rx.icon("lightbulb", size=14, color="var(--amber-9)"),
                            rx.text("Insights", size="2", weight="bold", color="var(--amber-11)"),
                            spacing="2",
                            align="center",
                        ),
                        rx.foreach(
                            message["insights"].to(list[dict[str, str]]),
                            _insight_item,
                        ),
                        width="100%",
                        spacing="1",
                        padding_top="8px",
                    ),
                ),

                # Data Story section (when story_mode is active)
                rx.cond(
                    (message["has_table"])
                    & (~message["is_streaming"])
                    & (ChatState.story_mode)
                    & (ChatState.story_context != ""),
                    _story_section(),
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


# Insight severity → color scheme
_SEVERITY_COLORS = {"info": "blue", "warning": "orange", "critical": "red"}


def _insight_item(insight: dict) -> rx.Component:
    """Render a single insight card."""
    return rx.hstack(
        rx.icon(
            rx.cond(
                insight["type"] == "anomaly", "triangle-alert",
                rx.cond(
                    insight["type"] == "trend", "trending-up",
                    rx.cond(
                        insight["type"] == "correlation", "git-branch",
                        rx.cond(
                            insight["type"] == "pareto", "pie-chart",
                            "bar-chart-3",
                        ),
                    ),
                ),
            ),
            size=12,
            color=rx.cond(
                insight["severity"] == "warning",
                "var(--orange-9)",
                rx.cond(
                    insight["severity"] == "critical",
                    "var(--red-9)",
                    "var(--blue-9)",
                ),
            ),
        ),
        rx.vstack(
            rx.text(insight["title"], size="1", weight="bold"),
            rx.text(insight["description"], size="1", color="var(--gray-11)"),
            spacing="0",
        ),
        spacing="2",
        align="start",
        padding="4px 8px",
        border_radius="6px",
        bg="var(--gray-a2)",
        width="100%",
    )


def _story_section() -> rx.Component:
    """Render data storytelling narrative section."""
    return rx.vstack(
        rx.separator(),
        rx.hstack(
            rx.icon("book-open", size=14, color="var(--violet-9)"),
            rx.text("Data Story", size="2", weight="bold", color="var(--violet-11)"),
            spacing="2",
            align="center",
        ),
        # Context
        rx.cond(
            ChatState.story_context != "",
            rx.text(
                ChatState.story_context,
                size="2",
                color="var(--gray-11)",
                padding="4px 0",
            ),
        ),
        # Key findings
        rx.cond(
            ChatState.story_key_findings.length() > 0,
            rx.vstack(
                rx.text("Key Findings", size="1", weight="bold", color="var(--gray-10)"),
                rx.foreach(
                    ChatState.story_key_findings,
                    lambda finding: rx.hstack(
                        rx.icon("circle-check", size=10, color="var(--green-9)"),
                        rx.text(finding, size="1", color="var(--gray-11)"),
                        spacing="2",
                        align="start",
                    ),
                ),
                spacing="1",
            ),
        ),
        # Implications
        rx.cond(
            ChatState.story_implications != "",
            rx.text(
                ChatState.story_implications,
                size="1",
                color="var(--gray-10)",
                font_style="italic",
            ),
        ),
        # Recommendations
        rx.cond(
            ChatState.story_recommendations.length() > 0,
            rx.vstack(
                rx.text("Recommendations", size="1", weight="bold", color="var(--accent-10)"),
                rx.foreach(
                    ChatState.story_recommendations,
                    lambda rec: rx.hstack(
                        rx.icon("arrow-right", size=10, color="var(--accent-9)"),
                        rx.text(rec, size="1", color="var(--gray-11)"),
                        spacing="2",
                        align="start",
                    ),
                ),
                spacing="1",
            ),
        ),
        width="100%",
        spacing="2",
        padding_top="8px",
    )


def _analysis_steps_section(message: dict) -> rx.Component:
    """Render multi-step analysis progress from per-message data."""
    return rx.vstack(
        rx.hstack(
            rx.icon("list-checks", size=14, color="var(--cyan-9)"),
            rx.text("Analysis Steps", size="2", weight="bold", color="var(--cyan-11)"),
            spacing="2",
            align="center",
        ),
        rx.foreach(
            message["analysis_steps"].to(list[dict[str, str]]),
            _analysis_step_item,
        ),
        width="100%",
        spacing="1",
        padding="8px 0",
        border_bottom="1px solid var(--gray-a3)",
    )


def _analysis_step_item(step: dict) -> rx.Component:
    """Render a single analysis step with status icon."""
    return rx.hstack(
        # Status icon
        rx.cond(
            step["status"].to(str) == "completed",
            rx.icon("circle-check", size=12, color="var(--green-9)"),
            rx.cond(
                step["status"].to(str) == "running",
                rx.spinner(size="1"),
                rx.cond(
                    step["status"].to(str) == "failed",
                    rx.icon("circle-x", size=12, color="var(--red-9)"),
                    rx.icon("circle", size=12, color="var(--gray-8)"),
                ),
            ),
        ),
        # Step number + description
        rx.vstack(
            rx.hstack(
                rx.text("Step ", step["step"].to(str), ": ", size="1", weight="bold"),
                rx.text(step["description"].to(str), size="1"),
                spacing="0",
            ),
            rx.cond(
                step["result_summary"].to(str) != "",
                rx.text(
                    step["result_summary"].to(str),
                    size="1",
                    color="var(--gray-9)",
                ),
            ),
            spacing="0",
        ),
        spacing="2",
        align="start",
        padding="2px 8px",
    )

"""Chat panel component with message list and input."""

import reflex as rx

from biai.state.chat import ChatState
from biai.state.query import QueryState
from biai.state.chart import ChartState
from biai.state.saved_queries import SavedQueriesState
from biai.components.chat_message import chat_message


def chat_panel() -> rx.Component:
    """Chat panel with message list and input."""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.icon("message-square", size=20, color="var(--accent-9)"),
            rx.text("Chat", size="4", weight="bold"),
            rx.spacer(),
            # Story mode toggle
            rx.tooltip(
                rx.icon_button(
                    rx.icon("book-open", size=14),
                    variant=rx.cond(ChatState.story_mode, "soft", "ghost"),
                    size="1",
                    on_click=ChatState.toggle_story_mode,
                    color=rx.cond(ChatState.story_mode, "var(--violet-9)", "inherit"),
                    aria_label="Toggle story mode",
                ),
                content="Toggle data storytelling",
            ),
            # Saved queries button
            rx.tooltip(
                rx.icon_button(
                    rx.icon("bookmark", size=14),
                    variant="ghost",
                    size="1",
                    on_click=[SavedQueriesState.load_saved_queries, SavedQueriesState.toggle_saved_panel],
                    aria_label="Saved queries",
                ),
                content="Saved queries",
            ),
            # Two-step clear: first click shows confirm, second click clears
            rx.cond(
                ChatState.confirm_clear,
                rx.hstack(
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("check", size=14),
                            variant="solid",
                            size="1",
                            color_scheme="red",
                            on_click=[ChatState.clear_chat, QueryState.clear_result, ChartState.clear_chart],
                            aria_label="Confirm clear",
                        ),
                        content="Confirm clear",
                    ),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("x", size=14),
                            variant="ghost",
                            size="1",
                            on_click=ChatState.cancel_clear_chat,
                            aria_label="Cancel clear",
                        ),
                        content="Cancel",
                    ),
                    spacing="1",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("trash-2", size=14),
                        variant="ghost",
                        size="1",
                        on_click=ChatState.request_clear_chat,
                        aria_label="Clear chat",
                    ),
                    content="Clear chat",
                ),
            ),
            width="100%",
            align="center",
            padding="12px 16px",
            border_bottom="1px solid var(--gray-a5)",
        ),

        # Saved queries panel (collapsible)
        rx.cond(
            SavedQueriesState.show_saved_panel,
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("bookmark", size=14, color="var(--accent-9)"),
                        rx.text("Saved Queries", size="2", weight="medium"),
                        rx.spacer(),
                        rx.icon_button(
                            rx.icon("x", size=12),
                            variant="ghost",
                            size="1",
                            on_click=SavedQueriesState.toggle_saved_panel,
                        ),
                        width="100%",
                        align="center",
                    ),
                    rx.cond(
                        SavedQueriesState.has_saved,
                        rx.vstack(
                            rx.foreach(
                                SavedQueriesState.saved_queries,
                                _saved_query_item,
                            ),
                            spacing="1",
                            width="100%",
                            max_height="200px",
                            overflow_y="auto",
                        ),
                        rx.text("No saved queries yet", size="1", color="var(--gray-9)"),
                    ),
                    spacing="2",
                    width="100%",
                ),
                padding="8px 16px",
                border_bottom="1px solid var(--gray-a5)",
                background="var(--gray-a2)",
            ),
        ),

        # Message list
        rx.box(
            rx.cond(
                ChatState.messages.length() == 0,
                _empty_state(),
                rx.vstack(
                    rx.foreach(ChatState.messages, chat_message),
                    width="100%",
                    spacing="2",
                    padding="16px",
                ),
            ),
            flex="1",
            overflow_y="auto",
            width="100%",
            tab_index=-1,
        ),

        # Suggested follow-up queries (drill-down)
        rx.cond(
            ChatState.suggested_queries.length() > 0,
            rx.box(
                rx.hstack(
                    rx.icon("lightbulb", size=12, color="var(--accent-9)"),
                    rx.text("Follow-up:", size="1", color="var(--gray-10)", weight="medium"),
                    spacing="1",
                    align="center",
                ),
                rx.hstack(
                    rx.foreach(
                        ChatState.suggested_queries,
                        _followup_chip,
                    ),
                    spacing="1",
                    flex_wrap="wrap",
                ),
                padding="6px 16px",
                border_top="1px solid var(--gray-a3)",
            ),
        ),

        # Input area
        rx.box(
            rx.form(
                rx.hstack(
                    rx.input(
                        placeholder="Ask a question about your data...",
                        name="question",
                        value=ChatState.input_value,
                        on_change=ChatState.set_input,
                        size="3",
                        width="100%",
                        disabled=ChatState.is_processing,
                    ),
                    rx.cond(
                        ChatState.is_streaming,
                        rx.tooltip(
                            rx.icon_button(
                                rx.icon("square", size=18),
                                type="button",
                                size="3",
                                color_scheme="red",
                                variant="outline",
                                on_click=ChatState.cancel_streaming,
                                aria_label="Stop streaming",
                            ),
                            content="Stop streaming",
                        ),
                        rx.tooltip(
                            rx.icon_button(
                                rx.cond(
                                    ChatState.is_processing,
                                    rx.spinner(size="2"),
                                    rx.icon("send-horizontal", size=18),
                                ),
                                type="submit",
                                disabled=ChatState.is_processing,
                                size="3",
                                aria_label="Send message",
                            ),
                            content="Send message",
                        ),
                    ),
                    width="100%",
                    spacing="2",
                    padding="12px 16px",
                ),
                on_submit=lambda _: ChatState.process_message(),
                reset_on_submit=False,
            ),
            border_top="1px solid var(--gray-a5)",
            width="100%",
        ),

        width="100%",
        height="100%",
        spacing="0",
    )


def _empty_state() -> rx.Component:
    """Empty chat state with welcome message."""
    return rx.center(
        rx.vstack(
            rx.icon("brain-circuit", size=48, color="var(--accent-9)", opacity=0.5),
            rx.heading("BIAI", size="6", weight="bold", color="var(--accent-9)"),
            rx.text(
                "Business Intelligence AI",
                size="3",
                color="var(--gray-11)",
            ),
            rx.text(
                "Ask questions about your data in natural language.",
                size="2",
                color="var(--gray-10)",
                text_align="center",
            ),
            rx.vstack(
                rx.text("Try asking:", size="2", weight="medium"),
                _suggestion("Show all tables and their row counts"),
                _suggestion("What are the top 10 most populated tables?"),
                _suggestion("Show column statistics for the largest table"),
                spacing="2",
                width="100%",
                padding_top="16px",
            ),
            align="center",
            spacing="3",
            max_width="400px",
        ),
        width="100%",
        height="100%",
    )


def _saved_query_item(query: rx.Var[dict]) -> rx.Component:
    """Render a saved query item."""
    return rx.hstack(
        rx.button(
            rx.icon("play", size=10),
            query["question"],
            variant="ghost",
            size="1",
            on_click=SavedQueriesState.run_saved_query(query["question"]),
            cursor="pointer",
            flex="1",
            justify_content="flex-start",
            overflow="hidden",
            text_overflow="ellipsis",
            white_space="nowrap",
        ),
        rx.icon_button(
            rx.icon("trash-2", size=10),
            variant="ghost",
            size="1",
            color_scheme="red",
            on_click=SavedQueriesState.delete_saved_query(query["id"]),
        ),
        width="100%",
        align="center",
        spacing="1",
    )


def _followup_chip(query: rx.Var[str]) -> rx.Component:
    """Clickable follow-up query suggestion."""
    return rx.button(
        rx.icon("arrow-right", size=10),
        query,
        variant="soft",
        size="1",
        on_click=ChatState.run_suggested_query(query),
        cursor="pointer",
    )


def _suggestion(text: str) -> rx.Component:
    """Suggestion chip."""
    return rx.button(
        rx.icon("sparkles", size=12),
        text,
        variant="outline",
        size="1",
        width="100%",
        on_click=[ChatState.set_input(text), ChatState.process_message],
    )

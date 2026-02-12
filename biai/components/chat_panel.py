"""Chat panel component with message list and input."""

import reflex as rx

from biai.state.chat import ChatState
from biai.state.query import QueryState
from biai.state.chart import ChartState
from biai.components.chat_message import chat_message


def chat_panel() -> rx.Component:
    """Chat panel with message list and input."""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.icon("message-square", size=20, color="var(--accent-9)"),
            rx.text("Chat", size="4", weight="bold"),
            rx.spacer(),
            # Two-step clear: first click shows confirm, second click clears
            rx.cond(
                ChatState.confirm_clear,
                rx.hstack(
                    rx.icon_button(
                        rx.icon("check", size=14),
                        variant="solid",
                        size="1",
                        color_scheme="red",
                        on_click=[ChatState.clear_chat, QueryState.clear_result, ChartState.clear_chart],
                        aria_label="Confirm clear",
                    ),
                    rx.icon_button(
                        rx.icon("x", size=14),
                        variant="ghost",
                        size="1",
                        on_click=ChatState.cancel_clear_chat,
                        aria_label="Cancel clear",
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
                _suggestion("Show top 10 customers by revenue"),
                _suggestion("What are the monthly sales trends?"),
                _suggestion("Which products have the highest profit margin?"),
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


def _suggestion(text: str) -> rx.Component:
    """Suggestion chip."""
    return rx.button(
        rx.icon("sparkles", size=12),
        text,
        variant="outline",
        size="1",
        width="100%",
        on_click=ChatState.set_input(text),
    )

"""Main layout with split-screen: sidebar + chat + dashboard."""

import reflex as rx

from biai.state.base import BaseState
from biai.components.sidebar import sidebar
from biai.components.chat_panel import chat_panel
from biai.components.dashboard_panel import dashboard_panel


def main_layout() -> rx.Component:
    """Main application layout: sidebar + split-screen (chat | dashboard)."""
    return rx.box(
        rx.hstack(
            # Sidebar
            rx.cond(
                BaseState.sidebar_open,
                sidebar(),
            ),
            # Main content area: split-screen
            rx.hstack(
                # Chat panel (left, 40%)
                rx.box(
                    chat_panel(),
                    width="40%",
                    height="100vh",
                    border_right="1px solid var(--gray-a5)",
                    overflow="hidden",
                ),
                # Dashboard panel (right, 60%)
                rx.box(
                    dashboard_panel(),
                    width="60%",
                    height="100vh",
                    overflow="hidden",
                ),
                width="100%",
                height="100vh",
                spacing="0",
            ),
            width="100%",
            height="100vh",
            spacing="0",
        ),
        width="100%",
        height="100vh",
        overflow="hidden",
        class_name="app-container",
    )

"""Sidebar component with connection, schema explorer, and settings."""

import reflex as rx

from biai.state.base import BaseState
from biai.state.database import DBState
from biai.state.schema import SchemaState
from biai.components.connection_form import connection_form
from biai.components.schema_explorer import schema_explorer
from biai.components.model_selector import model_selector


def sidebar() -> rx.Component:
    """Application sidebar."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.icon("brain-circuit", size=24, color="var(--accent-9)"),
                rx.heading("BIAI", size="5", weight="bold"),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("panel-left-close", size=16),
                    variant="ghost",
                    size="1",
                    on_click=BaseState.toggle_sidebar,
                ),
                width="100%",
                align="center",
                padding="12px 16px",
            ),
            rx.separator(),

            # Navigation tabs
            rx.hstack(
                _sidebar_tab("database", "Connection", "connection"),
                _sidebar_tab("table-2", "Schema", "schema"),
                _sidebar_tab("settings", "Settings", "settings"),
                width="100%",
                padding="4px 8px",
                spacing="2",
            ),
            rx.separator(),

            # Content based on active section
            rx.box(
                rx.cond(
                    BaseState.sidebar_section == "connection",
                    rx.vstack(
                        connection_form(),
                        rx.separator(),
                        model_selector(),
                        width="100%",
                        spacing="4",
                    ),
                ),
                rx.cond(
                    BaseState.sidebar_section == "schema",
                    schema_explorer(),
                ),
                rx.cond(
                    BaseState.sidebar_section == "settings",
                    _settings_panel(),
                ),
                flex="1",
                overflow_y="auto",
                padding="12px",
                width="100%",
            ),

            # Footer: connection status
            rx.separator(),
            rx.hstack(
                rx.cond(
                    DBState.is_connected,
                    rx.hstack(
                        rx.box(width="8px", height="8px", border_radius="50%", bg="green.9"),
                        rx.text("Connected", size="1", color="green.11"),
                        spacing="2",
                        align="center",
                    ),
                    rx.hstack(
                        rx.box(width="8px", height="8px", border_radius="50%", bg="gray.8"),
                        rx.text("Disconnected", size="1", color="gray.11"),
                        spacing="2",
                        align="center",
                    ),
                ),
                padding="8px 16px",
                width="100%",
            ),
            width="100%",
            height="100vh",
            spacing="0",
        ),
        width="280px",
        min_width="280px",
        height="100vh",
        border_right="1px solid var(--gray-a5)",
        bg="var(--color-panel)",
    )


def _sidebar_tab(icon_name: str, label: str, section: str) -> rx.Component:
    """Sidebar navigation tab."""
    return rx.button(
        rx.icon(icon_name, size=14),
        rx.text(label, size="1"),
        variant=rx.cond(BaseState.sidebar_section == section, "soft", "ghost"),
        size="1",
        on_click=BaseState.set_sidebar_section(section),
        flex="1",
    )


def _settings_panel() -> rx.Component:
    """Settings section in sidebar."""
    return rx.vstack(
        rx.text("Settings", size="3", weight="bold"),

        # Dark mode toggle
        rx.hstack(
            rx.text("Dark mode", size="2"),
            rx.spacer(),
            rx.color_mode.switch(),
            width="100%",
            align="center",
        ),

        width="100%",
        spacing="3",
        padding="8px",
    )

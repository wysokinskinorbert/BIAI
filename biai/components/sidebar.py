"""Sidebar component with connection, schema explorer, and settings."""

import reflex as rx

from biai.state.base import BaseState
from biai.state.database import DBState
from biai.components.connection_form import connection_form
from biai.components.schema_explorer import schema_explorer
from biai.components.model_selector import model_selector
from biai.pages.settings import SettingsState


def sidebar() -> rx.Component:
    """Application sidebar."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.icon("brain-circuit", size=24, color="var(--accent-9)"),
                rx.heading("BIAI", size="5", weight="bold"),
                rx.spacer(),
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("panel-left-close", size=16),
                        variant="ghost",
                        size="1",
                        on_click=BaseState.toggle_sidebar,
                        aria_label="Collapse sidebar",
                    ),
                    content="Collapse sidebar",
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

            # Content based on active section (all rendered, CSS display toggles visibility)
            rx.box(
                rx.box(
                    rx.vstack(
                        connection_form(),
                        rx.separator(),
                        model_selector(),
                        width="100%",
                        spacing="4",
                    ),
                    display=rx.cond(BaseState.sidebar_section == "connection", "block", "none"),
                    width="100%",
                ),
                rx.box(
                    schema_explorer(),
                    display=rx.cond(BaseState.sidebar_section == "schema", "block", "none"),
                    width="100%",
                ),
                rx.box(
                    _settings_panel(),
                    display=rx.cond(BaseState.sidebar_section == "settings", "block", "none"),
                    width="100%",
                ),
                flex="1",
                overflow_y="auto",
                padding="12px",
                width="100%",
                tab_index=-1,
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
        class_name="sidebar",
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

        # Appearance
        _sidebar_settings_section(
            "Appearance", "palette",
            rx.hstack(
                rx.text("Dark mode", size="2"),
                rx.spacer(),
                rx.color_mode.switch(),
                width="100%",
                align="center",
            ),
        ),

        # Ollama LLM
        _sidebar_settings_section(
            "Ollama LLM", "brain",
            _sidebar_field("Host", SettingsState.settings_ollama_host, SettingsState.set_ollama_host),
            _sidebar_field("Model", SettingsState.settings_ollama_model, SettingsState.set_ollama_model),
        ),

        # ChromaDB
        _sidebar_settings_section(
            "ChromaDB", "database",
            _sidebar_field("Host", SettingsState.settings_chroma_host, SettingsState.set_chroma_host),
            _sidebar_field("Collection", SettingsState.settings_chroma_collection, SettingsState.set_chroma_collection),
        ),

        # Query Execution
        _sidebar_settings_section(
            "Query", "timer",
            _sidebar_field("Timeout (s)", SettingsState.settings_query_timeout, SettingsState.set_query_timeout),
            _sidebar_field("Row limit", SettingsState.settings_row_limit, SettingsState.set_row_limit),
        ),

        # Action buttons
        rx.hstack(
            rx.button(
                rx.icon("save", size=14),
                "Save",
                on_click=SettingsState.save_settings,
                size="1",
                flex="1",
            ),
            rx.button(
                rx.icon("rotate-ccw", size=14),
                "Reset",
                on_click=SettingsState.reset_defaults,
                variant="outline",
                size="1",
                flex="1",
            ),
            width="100%",
            spacing="2",
        ),

        # Status message
        rx.callout(
            SettingsState.save_message,
            icon="check",
            color_scheme="green",
            size="1",
            width="100%",
            display=rx.cond(SettingsState.save_message != "", "flex", "none"),
        ),

        width="100%",
        spacing="3",
        padding="8px",
    )


def _sidebar_settings_section(title: str, icon_name: str, *children) -> rx.Component:
    """Compact settings section for sidebar."""
    return rx.vstack(
        rx.hstack(
            rx.icon(icon_name, size=14, color="var(--accent-9)"),
            rx.text(title, size="2", weight="medium"),
            align="center",
            spacing="2",
        ),
        *children,
        width="100%",
        spacing="2",
        padding="8px",
        border="1px solid var(--gray-a5)",
        border_radius="var(--radius-2)",
    )


def _sidebar_field(label: str, value, on_change) -> rx.Component:
    """Compact settings field for sidebar."""
    return rx.vstack(
        rx.text(label, size="1", color="var(--gray-11)"),
        rx.input(
            value=value,
            on_change=on_change,
            size="1",
            width="100%",
        ),
        width="100%",
        spacing="1",
    )

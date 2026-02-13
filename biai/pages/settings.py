"""Settings page with real configuration options."""

import reflex as rx

from biai.config.constants import (
    DEFAULT_MODEL, DEFAULT_OLLAMA_HOST, DEFAULT_CHROMA_HOST,
    DEFAULT_CHROMA_COLLECTION, QUERY_TIMEOUT, ROW_LIMIT,
)


class SettingsState(rx.State):
    """State for application settings."""

    # Ollama
    settings_ollama_host: str = DEFAULT_OLLAMA_HOST
    settings_ollama_model: str = DEFAULT_MODEL

    # ChromaDB
    settings_chroma_host: str = DEFAULT_CHROMA_HOST
    settings_chroma_collection: str = DEFAULT_CHROMA_COLLECTION

    # Query (stored as str for input binding)
    settings_query_timeout: str = str(QUERY_TIMEOUT)
    settings_row_limit: str = str(ROW_LIMIT)

    # Status
    save_message: str = ""

    def set_ollama_host(self, value: str):
        self.settings_ollama_host = value

    def set_ollama_model(self, value: str):
        self.settings_ollama_model = value

    def set_chroma_host(self, value: str):
        self.settings_chroma_host = value

    def set_chroma_collection(self, value: str):
        self.settings_chroma_collection = value

    def set_query_timeout(self, value: str):
        self.settings_query_timeout = value

    def set_row_limit(self, value: str):
        self.settings_row_limit = value

    async def save_settings(self):
        from biai.state.model import ModelState
        model_state = await self.get_state(ModelState)
        model_state.ollama_host = self.settings_ollama_host
        model_state.selected_model = self.settings_ollama_model
        self.save_message = "Settings saved successfully."

    async def reset_defaults(self):
        self.settings_ollama_host = DEFAULT_OLLAMA_HOST
        self.settings_ollama_model = DEFAULT_MODEL
        self.settings_chroma_host = DEFAULT_CHROMA_HOST
        self.settings_chroma_collection = DEFAULT_CHROMA_COLLECTION
        self.settings_query_timeout = str(QUERY_TIMEOUT)
        self.settings_row_limit = str(ROW_LIMIT)
        self.save_message = "Settings reset to defaults."
        # Propagate defaults back to ModelState
        from biai.state.model import ModelState
        model_state = await self.get_state(ModelState)
        model_state.ollama_host = self.settings_ollama_host
        model_state.selected_model = self.settings_ollama_model


def _settings_section(title: str, icon_name: str, *children) -> rx.Component:
    """Reusable settings section card."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon(icon_name, size=18, color="var(--accent-9)"),
                rx.text(title, size="3", weight="bold"),
                align="center",
                spacing="2",
            ),
            *children,
            width="100%",
            spacing="3",
        ),
        width="100%",
    )


def _field(label: str, value, on_change, placeholder: str = "") -> rx.Component:
    """Reusable settings field."""
    return rx.vstack(
        rx.text(label, size="2", color="var(--gray-11)"),
        rx.input(
            value=value,
            on_change=on_change,
            placeholder=placeholder,
            size="2",
            width="100%",
        ),
        width="100%",
        spacing="1",
    )


def settings_page() -> rx.Component:
    """Full settings page."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.link(
                    rx.icon("arrow-left", size=18),
                    href="/",
                ),
                rx.heading("Settings", size="5"),
                align="center",
                spacing="3",
                padding="16px 24px",
                border_bottom="1px solid var(--gray-a5)",
                width="100%",
            ),

            # Settings content
            rx.box(
                rx.vstack(
                    # Ollama section
                    _settings_section(
                        "Ollama LLM",
                        "brain",
                        _field(
                            "Host",
                            SettingsState.settings_ollama_host,
                            SettingsState.set_ollama_host,
                            DEFAULT_OLLAMA_HOST,
                        ),
                        _field(
                            "Model",
                            SettingsState.settings_ollama_model,
                            SettingsState.set_ollama_model,
                            DEFAULT_MODEL,
                        ),
                    ),

                    # ChromaDB section
                    _settings_section(
                        "ChromaDB Vector Store",
                        "database",
                        _field(
                            "Host",
                            SettingsState.settings_chroma_host,
                            SettingsState.set_chroma_host,
                            DEFAULT_CHROMA_HOST,
                        ),
                        _field(
                            "Collection name",
                            SettingsState.settings_chroma_collection,
                            SettingsState.set_chroma_collection,
                            DEFAULT_CHROMA_COLLECTION,
                        ),
                    ),

                    # Query section
                    _settings_section(
                        "Query Execution",
                        "timer",
                        _field(
                            "Timeout (seconds)",
                            SettingsState.settings_query_timeout,
                            SettingsState.set_query_timeout,
                            str(QUERY_TIMEOUT),
                        ),
                        _field(
                            "Row limit",
                            SettingsState.settings_row_limit,
                            SettingsState.set_row_limit,
                            str(ROW_LIMIT),
                        ),
                    ),

                    # Theme section
                    _settings_section(
                        "Appearance",
                        "palette",
                        rx.hstack(
                            rx.text("Dark mode", size="2"),
                            rx.spacer(),
                            rx.color_mode.switch(),
                            width="100%",
                            align="center",
                        ),
                    ),

                    # Action buttons
                    rx.hstack(
                        rx.button(
                            rx.icon("save", size=14),
                            "Save",
                            on_click=SettingsState.save_settings,
                            size="2",
                        ),
                        rx.button(
                            rx.icon("rotate-ccw", size=14),
                            "Reset to defaults",
                            on_click=SettingsState.reset_defaults,
                            variant="outline",
                            size="2",
                        ),
                        spacing="3",
                    ),

                    # Status message (CSS display to match sidebar pattern)
                    rx.callout(
                        SettingsState.save_message,
                        icon="check",
                        color_scheme="green",
                        size="1",
                        width="100%",
                        display=rx.cond(SettingsState.save_message != "", "flex", "none"),
                    ),

                    width="100%",
                    max_width="600px",
                    spacing="4",
                    padding="24px",
                ),
                flex="1",
                overflow_y="auto",
                width="100%",
                display="flex",
                justify_content="center",
            ),

            width="100%",
            height="100vh",
            spacing="0",
        ),
        width="100%",
        height="100vh",
    )

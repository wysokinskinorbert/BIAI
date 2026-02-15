"""Settings page with real configuration options."""

import reflex as rx

from biai.ai.language import normalize_language_enforcement_mode, normalize_response_language
from biai.config.constants import (
    DEFAULT_MODEL, DEFAULT_OLLAMA_HOST, DEFAULT_CHROMA_HOST,
    DEFAULT_CHROMA_COLLECTION, DEFAULT_NLG_MODEL, QUERY_TIMEOUT, ROW_LIMIT,
)
from biai.config.settings import get_settings, save_env_setting

_settings = get_settings()


class SettingsState(rx.State):
    """State for application settings."""

    # Ollama
    settings_ollama_host: str = _settings.ollama_host
    settings_ollama_sql_model: str = _settings.ollama_sql_model or _settings.ollama_model
    settings_ollama_nlg_model: str = _settings.ollama_nlg_model

    # ChromaDB
    settings_chroma_host: str = _settings.chroma_host
    settings_chroma_collection: str = _settings.chroma_collection

    # Query (stored as str for input binding)
    settings_query_timeout: str = str(_settings.query_timeout)
    settings_row_limit: str = str(_settings.query_row_limit)

    # Language
    settings_response_language: str = normalize_response_language(_settings.response_language)
    settings_language_enforcement_mode: str = normalize_language_enforcement_mode(
        _settings.language_enforcement_mode
    )

    # Status
    save_message: str = ""

    def set_ollama_host(self, value: str):
        self.settings_ollama_host = value

    def set_ollama_sql_model(self, value: str):
        self.settings_ollama_sql_model = value

    def set_ollama_nlg_model(self, value: str):
        self.settings_ollama_nlg_model = value

    # Backward-compatible alias for existing bindings
    def set_ollama_model(self, value: str):
        self.settings_ollama_sql_model = value

    def set_chroma_host(self, value: str):
        self.settings_chroma_host = value

    def set_chroma_collection(self, value: str):
        self.settings_chroma_collection = value

    def set_query_timeout(self, value: str):
        self.settings_query_timeout = value

    def set_row_limit(self, value: str):
        self.settings_row_limit = value

    def set_response_language(self, value: str):
        self.settings_response_language = normalize_response_language(value)

    def set_language_enforcement_mode(self, value: str):
        self.settings_language_enforcement_mode = normalize_language_enforcement_mode(value)

    async def save_settings(self):
        from biai.state.model import ModelState
        timeout = QUERY_TIMEOUT
        row_limit = ROW_LIMIT
        try:
            timeout = int(self.settings_query_timeout)
        except ValueError:
            timeout = QUERY_TIMEOUT
        try:
            row_limit = int(self.settings_row_limit)
        except ValueError:
            row_limit = ROW_LIMIT

        save_env_setting("OLLAMA_HOST", self.settings_ollama_host)
        save_env_setting("OLLAMA_MODEL", self.settings_ollama_sql_model)
        save_env_setting("OLLAMA_SQL_MODEL", self.settings_ollama_sql_model)
        save_env_setting("OLLAMA_NLG_MODEL", self.settings_ollama_nlg_model)
        save_env_setting("CHROMA_HOST", self.settings_chroma_host)
        save_env_setting("CHROMA_COLLECTION", self.settings_chroma_collection)
        save_env_setting("QUERY_TIMEOUT", str(timeout))
        save_env_setting("QUERY_ROW_LIMIT", str(row_limit))
        save_env_setting("RESPONSE_LANGUAGE", self.settings_response_language)
        save_env_setting("LANGUAGE_ENFORCEMENT_MODE", self.settings_language_enforcement_mode)

        model_state = await self.get_state(ModelState)
        model_state.ollama_host = self.settings_ollama_host
        model_state.selected_model = self.settings_ollama_sql_model
        model_state.selected_nlg_model = self.settings_ollama_nlg_model
        model_state.suggested_model = self.settings_ollama_sql_model
        self.save_message = "Settings saved successfully."

    async def reset_defaults(self):
        self.settings_ollama_host = DEFAULT_OLLAMA_HOST
        self.settings_ollama_sql_model = DEFAULT_MODEL
        self.settings_ollama_nlg_model = DEFAULT_NLG_MODEL
        self.settings_chroma_host = DEFAULT_CHROMA_HOST
        self.settings_chroma_collection = DEFAULT_CHROMA_COLLECTION
        self.settings_query_timeout = str(QUERY_TIMEOUT)
        self.settings_row_limit = str(ROW_LIMIT)
        self.settings_response_language = "pl"
        self.settings_language_enforcement_mode = "strict"
        self.save_message = "Settings reset to defaults."
        # Propagate defaults back to ModelState
        from biai.state.model import ModelState
        model_state = await self.get_state(ModelState)
        model_state.ollama_host = self.settings_ollama_host
        model_state.selected_model = self.settings_ollama_sql_model
        model_state.selected_nlg_model = self.settings_ollama_nlg_model
        model_state.suggested_model = self.settings_ollama_sql_model


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
                            "SQL model",
                            SettingsState.settings_ollama_sql_model,
                            SettingsState.set_ollama_sql_model,
                            DEFAULT_MODEL,
                        ),
                        _field(
                            "Response model",
                            SettingsState.settings_ollama_nlg_model,
                            SettingsState.set_ollama_nlg_model,
                            DEFAULT_NLG_MODEL,
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

                    # Language section
                    _settings_section(
                        "Language",
                        "languages",
                        rx.vstack(
                            rx.text("LLM response language", size="2", color="var(--gray-11)"),
                            rx.select(
                                ["pl", "en"],
                                value=SettingsState.settings_response_language,
                                on_change=SettingsState.set_response_language,
                                size="2",
                                width="100%",
                            ),
                            rx.text("Language enforcement mode", size="2", color="var(--gray-11)"),
                            rx.select(
                                ["strict", "best_effort"],
                                value=SettingsState.settings_language_enforcement_mode,
                                on_change=SettingsState.set_language_enforcement_mode,
                                size="2",
                                width="100%",
                            ),
                            width="100%",
                            spacing="1",
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

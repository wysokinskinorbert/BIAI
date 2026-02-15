"""Ollama model state."""

import reflex as rx

from biai.ai.model_profiles import get_model_profile
from biai.config.settings import get_settings, save_env_setting

# Read saved settings (from .env or defaults)
_settings = get_settings()
_default_sql_model = _settings.ollama_sql_model or _settings.ollama_model
_default_nlg_model = _settings.ollama_nlg_model


class ModelState(rx.State):
    """State for Ollama model selection."""

    available_models: list[str] = list(dict.fromkeys([_default_sql_model, _default_nlg_model]))
    selected_model: str = _default_sql_model  # SQL model
    selected_nlg_model: str = _default_nlg_model  # language/response model
    suggested_model: str = _default_sql_model
    suggestion_source_db: str = "postgresql"
    suggestion_label: str = "PostgreSQL"
    ollama_host: str = _settings.ollama_host
    is_loading: bool = False
    error: str = ""

    def set_model(self, model: str):
        """Set SQL model (backward compatible handler name)."""
        self.selected_model = model

    def set_nlg_model(self, model: str):
        """Set language/response model."""
        self.selected_nlg_model = model

    def set_ollama_host(self, value: str):
        self.ollama_host = value

    def suggest_profile_for_db(self, db_type: str):
        """Update suggestion based on active DB connector (no auto-override)."""
        profile = get_model_profile(db_type)
        self.suggested_model = profile.suggested_model
        self.suggestion_source_db = profile.db_type
        self.suggestion_label = profile.label

    def apply_suggested_model(self):
        """Apply suggested model explicitly (manual opt-in)."""
        if self.suggested_model:
            self.selected_model = self.suggested_model

    @rx.var
    def has_model_suggestion(self) -> bool:
        return bool(self.suggested_model)

    @rx.var
    def can_apply_suggestion(self) -> bool:
        return self.suggested_model != "" and self.suggested_model != self.selected_model

    @rx.var
    def suggestion_text(self) -> str:
        if not self.suggested_model:
            return ""
        return f"Suggested SQL model for {self.suggestion_label}: {self.suggested_model}"

    def save_as_default(self):
        """Save current model and host as defaults in .env."""
        try:
            save_env_setting("OLLAMA_SQL_MODEL", self.selected_model)
            save_env_setting("OLLAMA_NLG_MODEL", self.selected_nlg_model)
            save_env_setting("OLLAMA_MODEL", self.selected_model)
            save_env_setting("OLLAMA_HOST", self.ollama_host)
            self.suggested_model = self.selected_model
            return rx.toast.success(
                "Saved SQL + response models as defaults",
                duration=3000,
            )
        except Exception as e:
            return rx.toast.error(
                f"Failed to save: {e}",
                duration=5000,
            )

    @rx.event(background=True)
    async def refresh_models(self):
        async with self:
            self.is_loading = True
            self.error = ""

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                host = ""
                async with self:
                    host = self.ollama_host
                resp = await client.get(f"{host}/api/tags", timeout=10)
                resp.raise_for_status()
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
                async with self:
                    if models:
                        self.available_models = models
                        pinned = [
                            self.suggested_model,
                            self.selected_model,
                            self.selected_nlg_model,
                        ]
                        for model in pinned:
                            if model and model not in self.available_models:
                                self.available_models = [model] + self.available_models
                    self.is_loading = False
        except Exception as e:
            async with self:
                self.error = f"Cannot connect to Ollama: {str(e)}"
                self.is_loading = False

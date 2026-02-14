"""Ollama model state."""

import reflex as rx

from biai.config.settings import get_settings, save_env_setting

# Read saved settings (from .env or defaults)
_settings = get_settings()


class ModelState(rx.State):
    """State for Ollama model selection."""

    available_models: list[str] = [_settings.ollama_model]
    selected_model: str = _settings.ollama_model
    ollama_host: str = _settings.ollama_host
    is_loading: bool = False
    error: str = ""

    def set_model(self, model: str):
        self.selected_model = model

    def set_ollama_host(self, value: str):
        self.ollama_host = value

    def save_as_default(self):
        """Save current model and host as defaults in .env."""
        try:
            save_env_setting("OLLAMA_MODEL", self.selected_model)
            save_env_setting("OLLAMA_HOST", self.ollama_host)
            return rx.toast.success(
                f"Saved as default: {self.selected_model}",
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
                    self.is_loading = False
        except Exception as e:
            async with self:
                self.error = f"Cannot connect to Ollama: {str(e)}"
                self.is_loading = False

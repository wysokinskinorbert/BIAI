"""Ollama model state."""

import reflex as rx

from biai.config.constants import DEFAULT_MODEL, DEFAULT_OLLAMA_HOST


class ModelState(rx.State):
    """State for Ollama model selection."""

    available_models: list[str] = [DEFAULT_MODEL]
    selected_model: str = DEFAULT_MODEL
    ollama_host: str = DEFAULT_OLLAMA_HOST
    is_loading: bool = False
    error: str = ""

    def set_model(self, model: str):
        self.selected_model = model

    def set_ollama_host(self, value: str):
        self.ollama_host = value

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

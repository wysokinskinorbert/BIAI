"""Ollama model selector component."""

import reflex as rx


class ModelState(rx.State):
    """State for Ollama model selection."""

    available_models: list[str] = ["qwen2.5-coder:7b-instruct-q4_K_M"]
    selected_model: str = "qwen2.5-coder:7b-instruct-q4_K_M"
    ollama_host: str = "http://localhost:11434"
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


def model_selector() -> rx.Component:
    """Ollama model selector."""
    return rx.vstack(
        rx.text("AI Model", size="3", weight="bold"),

        # Ollama host
        rx.input(
            placeholder="Ollama host",
            value=ModelState.ollama_host,
            on_change=ModelState.set_ollama_host,
            size="2",
            width="100%",
        ),

        # Model selector
        rx.hstack(
            rx.select(
                ModelState.available_models,
                value=ModelState.selected_model,
                on_change=ModelState.set_model,
                size="2",
                width="100%",
            ),
            rx.icon_button(
                rx.icon("refresh-cw", size=14),
                on_click=ModelState.refresh_models,
                loading=ModelState.is_loading,
                variant="ghost",
                size="2",
            ),
            width="100%",
            spacing="2",
        ),

        # Error
        rx.cond(
            ModelState.error != "",
            rx.text(ModelState.error, size="1", color="red.11"),
        ),

        width="100%",
        spacing="2",
    )

"""Ollama model selector component."""

import reflex as rx

from biai.state.model import ModelState


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
            rx.tooltip(
                rx.icon_button(
                    rx.icon("refresh-cw", size=14),
                    on_click=ModelState.refresh_models,
                    loading=ModelState.is_loading,
                    variant="ghost",
                    size="2",
                    aria_label="Refresh models",
                ),
                content="Refresh models",
            ),
            width="100%",
            spacing="2",
        ),

        # Save as default
        rx.tooltip(
            rx.button(
                rx.icon("save", size=14),
                "Set as default",
                on_click=ModelState.save_as_default,
                variant="ghost",
                size="1",
                width="100%",
            ),
            content="Save selected model as default (in .env)",
        ),

        # Error (CSS display to avoid ghost a11y node)
        rx.callout(
            ModelState.error,
            icon="triangle-alert",
            color_scheme="red",
            size="1",
            width="100%",
            display=rx.cond(ModelState.error != "", "flex", "none"),
        ),

        width="100%",
        spacing="2",
    )

"""Ollama model selector component."""

import reflex as rx

from biai.state.model import ModelState


def model_selector() -> rx.Component:
    """Ollama model selector."""
    return rx.vstack(
        rx.text("AI Models", size="3", weight="bold"),

        # Ollama host
        rx.input(
            placeholder="Ollama host",
            value=ModelState.ollama_host,
            on_change=ModelState.set_ollama_host,
            size="2",
            width="100%",
        ),

        # Model selector
        rx.text("SQL model", size="1", color="var(--gray-11)"),
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

        rx.text("Response model", size="1", color="var(--gray-11)"),
        rx.select(
            ModelState.available_models,
            value=ModelState.selected_nlg_model,
            on_change=ModelState.set_nlg_model,
            size="2",
            width="100%",
        ),

        # Dialect-aware suggestion (manual apply)
        rx.vstack(
            rx.box(
                rx.hstack(
                    rx.icon("lightbulb", size=12, color="var(--blue-9)"),
                    rx.text(
                        ModelState.suggestion_text,
                        size="1",
                        color="var(--blue-11)",
                    ),
                    width="100%",
                    spacing="2",
                    align="center",
                ),
                width="100%",
                padding="8px",
                border_radius="var(--radius-2)",
                border="1px solid var(--blue-a5)",
                bg="var(--blue-a2)",
            ),
            rx.button(
                rx.icon("sparkles", size=12),
                "Apply suggested SQL model",
                on_click=ModelState.apply_suggested_model,
                size="1",
                variant="soft",
                width="100%",
                display=rx.cond(ModelState.can_apply_suggestion, "flex", "none"),
            ),
            width="100%",
            spacing="2",
            display=rx.cond(ModelState.has_model_suggestion, "flex", "none"),
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
            content="Save SQL + response models as defaults (in .env)",
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

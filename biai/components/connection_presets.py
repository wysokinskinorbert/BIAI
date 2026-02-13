"""Connection presets component - save/load/edit/delete connection configs."""

import reflex as rx

from biai.state.presets import PresetsState


def connection_presets() -> rx.Component:
    """Saved connections section with CRUD controls."""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.icon("bookmark", size=14, color="var(--accent-9)"),
            rx.text("Saved Connections", size="2", weight="bold"),
            rx.spacer(),
            rx.tooltip(
                rx.icon_button(
                    rx.icon("save", size=14),
                    variant="ghost",
                    size="1",
                    on_click=PresetsState.open_save_dialog,
                    aria_label="Save current connection",
                ),
                content="Save current connection",
            ),
            width="100%",
            align="center",
        ),

        # Preset list
        rx.cond(
            PresetsState.presets.length() > 0,
            rx.vstack(
                rx.foreach(PresetsState.presets, _preset_item),
                width="100%",
                spacing="1",
                max_height="25vh",
                overflow_y="auto",
            ),
            rx.text(
                "No saved connections",
                size="1",
                color="var(--gray-9)",
                width="100%",
                text_align="center",
                padding_y="8px",
            ),
        ),

        # Success / info message
        rx.callout(
            PresetsState.preset_message,
            icon="check",
            color_scheme="green",
            size="1",
            width="100%",
            display=rx.cond(PresetsState.preset_message != "", "flex", "none"),
        ),

        # Dialogs (rendered but hidden until opened)
        _save_dialog(),
        _delete_confirm_dialog(),

        width="100%",
        spacing="2",
        on_mount=PresetsState.load_presets,
    )


def _preset_item(preset: dict) -> rx.Component:
    """Single preset row in the list."""
    return rx.hstack(
        # Clickable area — loads the preset
        rx.hstack(
            rx.cond(
                preset["db_type"] == "postgresql",
                rx.icon("database", size=14, color="var(--blue-9)"),
                rx.icon("database", size=14, color="var(--orange-9)"),
            ),
            rx.text(preset["name"], size="2", weight="medium", truncate=True),
            flex="1",
            align="center",
            spacing="2",
            cursor="pointer",
            on_click=PresetsState.load_preset(preset["id"]),
        ),
        # Edit
        rx.icon_button(
            rx.icon("pencil", size=12),
            variant="ghost",
            size="1",
            on_click=PresetsState.open_edit_dialog(preset["id"]),
            aria_label="Edit preset",
        ),
        # Delete
        rx.icon_button(
            rx.icon("trash-2", size=12),
            variant="ghost",
            size="1",
            color_scheme="red",
            on_click=PresetsState.open_delete_confirm(preset["id"]),
            aria_label="Delete preset",
        ),
        width="100%",
        align="center",
        padding="4px 8px",
        border_radius="6px",
        _hover={"bg": "var(--gray-a3)"},
    )


def _save_dialog() -> rx.Component:
    """Dialog for saving / renaming a connection preset."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Save Connection"),
            rx.dialog.description(
                "Enter a name for this connection preset.",
            ),
            rx.flex(
                rx.input(
                    placeholder="e.g., Production PostgreSQL",
                    value=PresetsState.preset_name,
                    on_change=PresetsState.set_preset_name,
                    size="2",
                    width="100%",
                    auto_focus=True,
                ),
                rx.callout(
                    PresetsState.preset_error,
                    icon="triangle-alert",
                    color_scheme="red",
                    size="1",
                    width="100%",
                    display=rx.cond(
                        PresetsState.preset_error != "", "flex", "none",
                    ),
                ),
                direction="column",
                spacing="3",
                width="100%",
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button("Cancel", variant="soft", color_scheme="gray"),
                ),
                rx.button("Save", on_click=PresetsState.save_preset),
                spacing="3",
                margin_top="16px",
                justify="end",
            ),
            max_width="420px",
        ),
        open=PresetsState.show_save_dialog,
        on_open_change=PresetsState.handle_save_dialog_change,
    )


def _delete_confirm_dialog() -> rx.Component:
    """Confirmation dialog for deleting a preset."""
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Delete Connection"),
            rx.alert_dialog.description(
                "Are you sure? This action cannot be undone.",
            ),
            rx.flex(
                rx.alert_dialog.cancel(
                    rx.button("Cancel", variant="soft", color_scheme="gray"),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        "Delete",
                        color_scheme="red",
                        on_click=PresetsState.confirm_delete,
                    ),
                ),
                spacing="3",
                margin_top="16px",
                justify="end",
            ),
        ),
        open=PresetsState.show_delete_confirm,
        on_open_change=PresetsState.handle_delete_dialog_change,
    )

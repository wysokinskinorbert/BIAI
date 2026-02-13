"""Connection presets state."""

import reflex as rx

from biai.state.database import DBState


class PresetsState(rx.State):
    """Manages saved connection presets."""

    presets: list[dict] = []
    show_save_dialog: bool = False
    show_delete_confirm: bool = False
    preset_name: str = ""
    editing_preset_id: str = ""
    delete_target_id: str = ""
    preset_error: str = ""
    preset_message: str = ""

    def set_preset_name(self, value: str):
        self.preset_name = value

    def load_presets(self):
        """Load presets from disk (on_mount)."""
        from biai.utils.connection_storage import ConnectionStorage

        self.presets = ConnectionStorage.load_all()
        self.preset_message = ""

    def open_save_dialog(self):
        """Open save dialog for a new preset."""
        self.preset_name = ""
        self.editing_preset_id = ""
        self.show_save_dialog = True
        self.preset_error = ""
        self.preset_message = ""

    def open_edit_dialog(self, preset_id: str):
        """Open save dialog pre-filled with the preset name."""
        for p in self.presets:
            if p["id"] == preset_id:
                self.preset_name = p["name"]
                break
        self.editing_preset_id = preset_id
        self.show_save_dialog = True
        self.preset_error = ""
        self.preset_message = ""

    def handle_save_dialog_change(self, is_open: bool):
        """Handle dialog open/close (including Escape / click-outside)."""
        self.show_save_dialog = is_open
        if not is_open:
            self.preset_name = ""
            self.editing_preset_id = ""
            self.preset_error = ""

    def open_delete_confirm(self, preset_id: str):
        """Open delete confirmation dialog."""
        self.delete_target_id = preset_id
        self.show_delete_confirm = True
        self.preset_message = ""

    def handle_delete_dialog_change(self, is_open: bool):
        """Handle delete dialog open/close."""
        self.show_delete_confirm = is_open
        if not is_open:
            self.delete_target_id = ""

    def confirm_delete(self):
        """Delete the target preset."""
        if self.delete_target_id:
            from biai.utils.connection_storage import ConnectionStorage

            self.presets = ConnectionStorage.delete(self.delete_target_id)
        self.show_delete_confirm = False
        self.delete_target_id = ""
        self.preset_message = "Preset deleted"

    @rx.event(background=True)
    async def save_preset(self):
        """Save current form fields as a preset (or update existing)."""
        async with self:
            name = self.preset_name.strip()
            editing_id = self.editing_preset_id
            if not name:
                self.preset_error = "Name is required"
                return

        # Read connection fields from DBState
        async with self:
            db_state = await self.get_state(DBState)

        async with db_state:
            data = {
                "db_type": db_state.db_type,
                "host": db_state.host,
                "port": db_state.port,
                "database": db_state.database,
                "username": db_state.username,
                "password": db_state.password,
                "dsn": db_state.dsn,
            }

        from biai.utils.connection_storage import ConnectionStorage
        from biai.utils.crypto import encrypt_password

        data["name"] = name
        data["password_encrypted"] = encrypt_password(data.pop("password"))

        if editing_id:
            presets = ConnectionStorage.update(editing_id, data)
        else:
            presets = ConnectionStorage.add(data)

        async with self:
            self.presets = presets
            self.show_save_dialog = False
            self.preset_name = ""
            self.editing_preset_id = ""
            self.preset_error = ""
            self.preset_message = "Preset saved!"

    @rx.event(background=True)
    async def load_preset(self, preset_id: str):
        """Load a preset into the connection form."""
        preset = None
        async with self:
            for p in self.presets:
                if p["id"] == preset_id:
                    preset = dict(p)
                    break

        if not preset:
            return

        from biai.utils.crypto import decrypt_password

        password = decrypt_password(preset.get("password_encrypted", ""))

        async with self:
            db_state = await self.get_state(DBState)

        async with db_state:
            db_state.db_type = preset["db_type"]
            db_state.host = preset["host"]
            db_state.port = preset["port"]
            db_state.database = preset["database"]
            db_state.username = preset["username"]
            db_state.password = password
            db_state.dsn = preset.get("dsn", "")
            db_state.connection_error = ""

        async with self:
            self.preset_message = f"Loaded: {preset['name']}"

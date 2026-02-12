"""Base application state."""

import reflex as rx


class BaseState(rx.State):
    """Base state with shared app-level properties."""

    # Sidebar
    sidebar_open: bool = True
    sidebar_section: str = "connection"  # connection | schema | settings

    # Global loading
    is_loading: bool = False

    # Notifications
    notification: str = ""
    notification_type: str = "info"  # info | success | error | warning

    def toggle_sidebar(self):
        self.sidebar_open = not self.sidebar_open

    def set_sidebar_section(self, section: str):
        self.sidebar_section = section

    def show_notification(self, message: str, ntype: str = "info"):
        self.notification = message
        self.notification_type = ntype

    def clear_notification(self):
        self.notification = ""

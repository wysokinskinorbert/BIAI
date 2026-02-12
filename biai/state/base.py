"""Base application state."""

import reflex as rx


class BaseState(rx.State):
    """Base state with shared app-level properties."""

    # Sidebar
    sidebar_open: bool = True
    sidebar_section: str = "connection"  # connection | schema | settings

    def toggle_sidebar(self):
        self.sidebar_open = not self.sidebar_open

    def set_sidebar_section(self, section: str):
        self.sidebar_section = section

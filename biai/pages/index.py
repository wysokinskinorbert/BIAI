"""Main page: split-screen layout."""

import reflex as rx

from biai.components.layout import main_layout


def index() -> rx.Component:
    """Main application page."""
    return main_layout()

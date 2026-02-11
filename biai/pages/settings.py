"""Settings page (post-MVP placeholder)."""

import reflex as rx


def settings_page() -> rx.Component:
    """Settings page - to be implemented in future versions."""
    return rx.center(
        rx.vstack(
            rx.heading("Settings", size="6"),
            rx.text("Settings page will be available in a future version.", color="var(--gray-11)"),
            rx.link("Back to main", href="/"),
            align="center",
            spacing="4",
        ),
        height="100vh",
    )

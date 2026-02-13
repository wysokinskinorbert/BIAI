"""Database connection form component."""

import reflex as rx

from biai.state.database import DBState
from biai.components.connection_presets import connection_presets


def connection_form() -> rx.Component:
    """Database connection form."""
    return rx.vstack(
        connection_presets(),
        rx.separator(),
        rx.text("Database Connection", size="3", weight="bold"),

        # DB Type selector
        rx.select(
            ["postgresql", "oracle"],
            value=DBState.db_type,
            on_change=DBState.set_db_type,
            width="100%",
            size="2",
        ),

        # Host
        rx.input(
            placeholder="Host *",
            value=DBState.host,
            on_change=DBState.set_host,
            size="2",
            width="100%",
            required=True,
        ),

        # Port
        rx.input(
            placeholder="Port",
            value=DBState.port.to(str),
            on_change=DBState.set_port,
            size="2",
            width="100%",
        ),

        # Database
        rx.input(
            placeholder="Database / Service Name *",
            value=DBState.database,
            on_change=DBState.set_database,
            size="2",
            width="100%",
            required=True,
        ),

        # Username
        rx.input(
            placeholder="Username *",
            value=DBState.username,
            on_change=DBState.set_username,
            size="2",
            width="100%",
            required=True,
        ),

        # Password
        rx.input(
            placeholder="Password",
            value=DBState.password,
            on_change=DBState.set_password,
            type="password",
            size="2",
            width="100%",
        ),

        # DSN (alternative)
        rx.input(
            placeholder="DSN (alternative to host/port/db)",
            value=DBState.dsn,
            on_change=DBState.set_dsn,
            size="2",
            width="100%",
        ),

        # Buttons
        rx.hstack(
            rx.tooltip(
                rx.button(
                    rx.cond(
                        DBState.is_connecting,
                        rx.spinner(size="1"),
                        rx.icon("plug", size=14),
                    ),
                    rx.cond(
                        DBState.is_connected,
                        "Reconnect",
                        "Connect",
                    ),
                    on_click=DBState.connect,
                    loading=DBState.is_connecting,
                    disabled=~DBState.can_connect,
                    size="2",
                    flex="1",
                ),
                content="Connect to database",
            ),
            rx.cond(
                DBState.is_connected,
                rx.tooltip(
                    rx.button(
                        rx.icon("unplug", size=14),
                        "Disconnect",
                        on_click=DBState.disconnect,
                        variant="outline",
                        color_scheme="red",
                        size="2",
                    ),
                    content="Disconnect from database",
                ),
            ),
            width="100%",
            spacing="2",
        ),

        # Connection error (CSS display instead of rx.cond to avoid ghost a11y node)
        rx.callout(
            DBState.connection_error,
            icon="triangle-alert",
            color_scheme="red",
            size="1",
            width="100%",
            display=rx.cond(DBState.connection_error != "", "flex", "none"),
        ),

        # Server version
        rx.cond(
            DBState.is_connected,
            rx.text(
                DBState.server_version,
                size="1",
                color="var(--gray-11)",
                trim="both",
            ),
        ),

        # Write permissions warning (CSS display to avoid ghost a11y node)
        rx.callout(
            "DB user has write permissions. Recommend using a read-only account.",
            icon="triangle-alert",
            color_scheme="orange",
            size="1",
            width="100%",
            display=rx.cond(
                DBState.is_connected & ~DBState.is_read_only,
                "flex",
                "none",
            ),
        ),

        width="100%",
        spacing="2",
    )

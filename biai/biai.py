"""BIAI - Business Intelligence AI: Application entry point."""

import reflex as rx

from biai.pages.index import index
from biai.pages.settings import settings_page
from biai.pages.dashboard import dashboard_page
from biai.pages.query_builder import builder_page


# Dark theme configuration
app = rx.App(
    theme=rx.theme(
        appearance="inherit",
        accent_color="violet",
        gray_color="slate",
        radius="medium",
        scaling="95%",
    ),
    style={
        "font_family": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "::selection": {
            "background": "var(--accent-5)",
        },
    },
    stylesheets=["/styles/global.css", "/styles/process-flow.css"],
)

app.add_page(index, route="/", title="BIAI - Business Intelligence AI")
app.add_page(settings_page, route="/settings", title="BIAI - Settings")
app.add_page(dashboard_page, route="/dashboard", title="BIAI - Dashboard Builder")
app.add_page(builder_page, route="/builder", title="BIAI - Query Builder")

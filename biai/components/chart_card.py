"""Chart card component with Plotly rendering."""

import reflex as rx

from biai.state.chart import ChartState


def chart_card() -> rx.Component:
    """Chart card with Plotly rendering."""
    return rx.card(
        rx.vstack(
            # Header
            rx.hstack(
                rx.icon("bar-chart-3", size=16, color="var(--accent-9)"),
                rx.text(ChartState.chart_title, size="3", weight="medium"),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("maximize-2", size=14),
                    variant="ghost",
                    size="1",
                    on_click=ChartState.toggle_fullscreen,
                ),
                width="100%",
                align="center",
            ),

            # Chart container - Plotly
            # Always render plotly (avoids React hooks order warning),
            # toggle visibility via CSS display instead of rx.cond
            rx.box(
                rx.plotly(
                    data=ChartState.plotly_figure,
                    key=ChartState.chart_version,
                ),
                width="100%",
                key=ChartState.chart_version,
                display=rx.cond(ChartState.show_plotly, "block", "none"),
            ),

            width="100%",
            spacing="3",
        ),
        width="100%",
    )

"""Chart card component with ECharts support."""

import reflex as rx

from biai.state.chart import ChartState


def chart_card() -> rx.Component:
    """Chart card with ECharts/Plotly rendering."""
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

            # Chart container
            rx.cond(
                ChartState.show_echarts,
                rx.box(
                    # ECharts placeholder - will be rendered via custom component
                    rx.el.div(
                        id="echarts-container",
                        style={
                            "width": "100%",
                            "height": "350px",
                            "background": "var(--gray-a2)",
                            "border_radius": "8px",
                        },
                    ),
                    width="100%",
                ),
            ),

            width="100%",
            spacing="3",
        ),
        width="100%",
    )

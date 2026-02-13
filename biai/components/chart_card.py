"""Chart card component with ECharts / Plotly dual rendering and fullscreen dialog."""

import reflex as rx

from biai.state.chart import ChartState
from biai.components.echarts.wrapper import echarts_component


def chart_card() -> rx.Component:
    """Chart card with ECharts (default) or Plotly rendering."""
    return rx.fragment(
        rx.card(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.icon("bar-chart-3", size=16, color="var(--accent-9)"),
                    rx.text(ChartState.chart_title, size="3", weight="medium"),
                    rx.spacer(),
                    # Engine badge
                    rx.badge(
                        ChartState.chart_engine,
                        variant="surface",
                        size="1",
                    ),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("maximize-2", size=14),
                            variant="ghost",
                            size="1",
                            on_click=ChartState.toggle_fullscreen,
                            cursor="pointer",
                        ),
                        content="Expand chart",
                    ),
                    width="100%",
                    align="center",
                ),

                # ECharts container (dimensions on wrapper box; ECharts fills parent)
                rx.box(
                    echarts_component(
                        option=ChartState.echarts_option,
                        not_merge=True,
                    ),
                    width="100%",
                    height="350px",
                    display=rx.cond(ChartState.show_echarts, "block", "none"),
                    key=ChartState.chart_version,
                ),

                # Plotly container (fallback for complex charts)
                rx.box(
                    rx.plotly(
                        data=ChartState.plotly_figure,
                        key=ChartState.chart_version,
                    ),
                    width="100%",
                    display=rx.cond(ChartState.show_plotly, "block", "none"),
                    key=ChartState.chart_version,
                ),

                width="100%",
                spacing="3",
            ),
            width="100%",
        ),

        # Fullscreen dialog
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(
                    rx.hstack(
                        rx.icon("bar-chart-3", size=18, color="var(--accent-9)"),
                        rx.text(ChartState.chart_title, size="4", weight="bold"),
                        rx.spacer(),
                        rx.dialog.close(
                            rx.icon_button(
                                rx.icon("x", size=16),
                                variant="ghost",
                                size="1",
                            ),
                        ),
                        width="100%",
                        align="center",
                    ),
                ),
                # Fullscreen ECharts
                rx.box(
                    echarts_component(
                        option=ChartState.echarts_option,
                        not_merge=True,
                    ),
                    width="100%",
                    height="500px",
                    display=rx.cond(ChartState.show_echarts, "block", "none"),
                ),
                # Fullscreen Plotly
                rx.box(
                    rx.plotly(
                        data=ChartState.plotly_figure,
                    ),
                    width="100%",
                    min_height="500px",
                    display=rx.cond(ChartState.show_plotly, "block", "none"),
                ),
                max_width="90vw",
                width="90vw",
            ),
            open=ChartState.show_fullscreen,
            on_open_change=ChartState.toggle_fullscreen,
        ),
    )

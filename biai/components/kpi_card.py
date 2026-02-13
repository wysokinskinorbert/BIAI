"""KPI card component for single-value query results."""

import reflex as rx

from biai.state.query import QueryState


def kpi_card() -> rx.Component:
    """Large KPI card for single-row/single-value results."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("trending-up", size=16, color="var(--accent-9)"),
                rx.text("Key Metric", size="3", weight="medium"),
                width="100%",
                align="center",
            ),
            rx.center(
                rx.vstack(
                    rx.foreach(
                        QueryState.kpi_items,
                        _kpi_item,
                    ),
                    spacing="4",
                    align="center",
                ),
                width="100%",
                padding="16px 0",
            ),
            width="100%",
            spacing="3",
        ),
        width="100%",
    )


def _kpi_item(item: list[str]) -> rx.Component:
    """Render a single KPI metric (label + value pair)."""
    return rx.vstack(
        rx.text(
            item[0],
            size="2",
            color="var(--gray-10)",
            weight="medium",
        ),
        rx.text(
            item[1],
            size="7",
            weight="bold",
            color="var(--accent-11)",
        ),
        align="center",
        spacing="1",
    )

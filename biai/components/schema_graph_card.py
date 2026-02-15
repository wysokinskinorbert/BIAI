"""Schema graph card - force-directed graph showing table topology."""

import reflex as rx

from biai.state.schema import SchemaState
from biai.components.echarts.wrapper import echarts_component


def schema_graph_card() -> rx.Component:
    """Card showing schema topology as an ECharts force-directed graph."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("network", size=16, color="var(--accent-9)"),
                rx.text("Schema Topology", size="3", weight="bold"),
                rx.spacer(),
                rx.cond(
                    SchemaState.graph_hub_count > 0,
                    rx.badge(
                        SchemaState.graph_hub_count.to(str),
                        " hubs",
                        variant="surface",
                        size="1",
                    ),
                ),
                rx.cond(
                    SchemaState.graph_communities > 0,
                    rx.badge(
                        SchemaState.graph_communities.to(str),
                        " domains",
                        variant="surface",
                        size="1",
                    ),
                ),
                width="100%",
                align="center",
            ),
            rx.box(
                echarts_component(
                    option=SchemaState.schema_graph_option,
                    not_merge=True,
                ),
                width="100%",
                height="400px",
            ),
            width="100%",
            spacing="3",
        ),
        width="100%",
    )

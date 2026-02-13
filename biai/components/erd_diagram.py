"""ERD (Entity-Relationship Diagram) card for the dashboard."""

import reflex as rx

from biai.state.schema import SchemaState
from biai.components.react_flow.wrapper import (
    react_flow,
    react_flow_background,
    react_flow_controls,
    react_flow_minimap,
    react_flow_provider,
)


def erd_card() -> rx.Component:
    """ERD diagram showing table relationships from schema."""
    return rx.box(
        # Header
        rx.hstack(
            rx.icon("database", size=16, color="var(--accent-9)"),
            rx.text("Database Schema", size="3", weight="bold"),
            rx.spacer(),
            rx.badge(
                SchemaState.table_count_label,
                variant="soft",
                size="1",
            ),
            width="100%",
            align="center",
            padding="8px 12px",
            border_bottom="1px solid var(--gray-a5)",
        ),
        # React Flow canvas
        rx.box(
            react_flow_provider(
                react_flow(
                    react_flow_background(
                        variant="dots",
                        gap=20,
                        color=rx.color_mode_cond("#ccc", "#333"),
                    ),
                    react_flow_controls(
                        show_zoom=True,
                        show_fit_view=True,
                        show_interactive=False,
                    ),
                    react_flow_minimap(
                        node_stroke_color=rx.color_mode_cond("#999", "#555"),
                        node_color=rx.color_mode_cond("#ccc", "#333"),
                    ),
                    nodes=SchemaState.erd_nodes,
                    edges=SchemaState.erd_edges,
                    node_types=rx.Var("erdNodeTypes"),
                    fit_view=True,
                    color_mode=rx.color_mode_cond("light", "dark"),
                    nodes_draggable=True,
                    nodes_connectable=False,
                ),
            ),
            width="100%",
            height="400px",
            border_radius="8px",
            overflow="hidden",
        ),
        # Footer with FK count
        rx.cond(
            SchemaState.erd_edge_count > 0,
            rx.hstack(
                rx.icon("link", size=14, color="var(--orange-9)"),
                rx.text(
                    SchemaState.erd_edge_count_label,
                    size="1",
                    color="var(--gray-10)",
                ),
                width="100%",
                padding="8px 12px",
                border_top="1px solid var(--gray-a5)",
                spacing="2",
                align="center",
            ),
        ),
        # Card container styles
        width="100%",
        border_radius="12px",
        bg="var(--gray-a2)",
        border="1px solid var(--gray-a5)",
        overflow="hidden",
    )

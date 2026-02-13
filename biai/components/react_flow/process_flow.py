"""Process Flow visualization card for the dashboard."""

import reflex as rx

from biai.state.process import ProcessState
from biai.components.react_flow.wrapper import (
    react_flow,
    react_flow_background,
    react_flow_controls,
    react_flow_minimap,
    react_flow_provider,
)


def process_flow_card() -> rx.Component:
    """Process flow visualization card with React Flow.

    Renders a dark-themed React Flow graph inside a card with:
    - Header: process name + layout toggle button
    - Body: interactive React Flow canvas (400px height)
    - Footer: metrics bar (bottleneck, total transitions)
    """
    return rx.box(
        # Header
        rx.hstack(
            rx.icon("workflow", size=16, color="var(--accent-9)"),
            rx.text(ProcessState.process_name, size="3", weight="bold"),
            rx.spacer(),
            rx.tooltip(
                rx.icon_button(
                    rx.icon("arrow-down-up", size=14),
                    variant="ghost",
                    size="1",
                    on_click=ProcessState.toggle_layout,
                ),
                content="Toggle vertical/horizontal layout",
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
                        variant="dots", gap=20,
                        color=rx.color_mode_cond("#ccc", "#333"),
                    ),
                    react_flow_controls(
                        show_zoom=True, show_fit_view=True, show_interactive=False
                    ),
                    react_flow_minimap(
                        node_stroke_color=rx.color_mode_cond("#999", "#555"),
                        node_color=rx.color_mode_cond("#ccc", "#333"),
                    ),
                    nodes=ProcessState.flow_nodes,
                    edges=ProcessState.flow_edges,
                    node_types=rx.Var("processNodeTypes"),
                    fit_view=True,
                    color_mode=rx.color_mode_cond("light", "dark"),
                    nodes_draggable=True,
                    nodes_connectable=False,
                    on_node_click=ProcessState.on_node_click,
                ),
            ),
            width="100%",
            height="400px",
            border_radius="8px",
            overflow="hidden",
        ),
        # Metrics bar
        rx.cond(
            ProcessState.has_metrics,
            rx.hstack(
                rx.cond(
                    ProcessState.bottleneck_label != "",
                    rx.hstack(
                        rx.icon("alert-triangle", size=14, color="#ef4444"),
                        rx.text(
                            "Bottleneck: ",
                            size="1",
                            color="var(--gray-10)",
                        ),
                        rx.text(
                            ProcessState.bottleneck_label,
                            size="1",
                            weight="bold",
                            color="#ef4444",
                        ),
                        spacing="1",
                        align="center",
                    ),
                ),
                rx.cond(
                    ProcessState.total_instances > 0,
                    rx.hstack(
                        rx.icon("layers", size=14, color="var(--accent-9)"),
                        rx.text(
                            ProcessState.total_instances_display,
                            size="1",
                            color="var(--gray-10)",
                        ),
                        spacing="1",
                        align="center",
                    ),
                ),
                rx.cond(
                    ProcessState.total_transitions > 0,
                    rx.hstack(
                        rx.icon(
                            "arrow-right-left", size=14, color="var(--gray-9)"
                        ),
                        rx.text(
                            ProcessState.total_transitions_display,
                            size="1",
                            color="var(--gray-10)",
                        ),
                        spacing="1",
                        align="center",
                    ),
                ),
                width="100%",
                padding="8px 12px",
                border_top="1px solid var(--gray-a5)",
                spacing="4",
                flex_wrap="wrap",
            ),
        ),
        # Selected node details
        rx.cond(
            ProcessState.has_selected_node,
            rx.hstack(
                rx.icon("info", size=14, color="var(--accent-9)"),
                rx.text(
                    ProcessState.selected_node_label,
                    size="1",
                    weight="bold",
                ),
                rx.cond(
                    ProcessState.selected_node_count != "",
                    rx.badge(
                        ProcessState.selected_node_count,
                        variant="soft",
                        size="1",
                    ),
                ),
                rx.cond(
                    ProcessState.selected_node_duration != "",
                    rx.badge(
                        ProcessState.selected_node_duration,
                        variant="outline",
                        size="1",
                    ),
                ),
                width="100%",
                padding="6px 12px",
                border_top="1px solid var(--gray-a5)",
                spacing="2",
                align="center",
                bg="var(--gray-a2)",
            ),
        ),
        # Card container styles
        width="100%",
        border_radius="12px",
        bg="var(--gray-a2)",
        border="1px solid var(--gray-a5)",
        overflow="hidden",
    )

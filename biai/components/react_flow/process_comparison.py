"""Process comparison — side-by-side view of current vs previous process."""

import reflex as rx

from biai.state.process import ProcessState
from biai.components.react_flow.wrapper import (
    react_flow,
    react_flow_background,
    react_flow_controls,
    react_flow_provider,
)


def _flow_panel(
    nodes_var,
    edges_var,
    name_var,
    label: str,
) -> rx.Component:
    """Single React Flow panel for comparison view."""
    return rx.box(
        rx.text(
            rx.text.strong(label), ": ", name_var,
            size="2",
            color="var(--gray-11)",
            padding="6px 12px",
        ),
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
                    nodes=nodes_var,
                    edges=edges_var,
                    node_types=rx.Var("processNodeTypes"),
                    fit_view=True,
                    color_mode=rx.color_mode_cond("light", "dark"),
                    nodes_draggable=False,
                    nodes_connectable=False,
                ),
            ),
            width="100%",
            height="350px",
            overflow="hidden",
        ),
        width="50%",
        border="1px solid var(--gray-a5)",
        border_radius="8px",
        overflow="hidden",
    )


def process_comparison_card() -> rx.Component:
    """Side-by-side comparison of previous and current process."""
    return rx.box(
        # Header
        rx.hstack(
            rx.icon("git-compare", size=16, color="var(--accent-9)"),
            rx.text("Process Comparison", size="3", weight="bold"),
            rx.spacer(),
            rx.icon_button(
                rx.icon("x", size=14),
                variant="ghost",
                size="1",
                on_click=ProcessState.toggle_comparison,
            ),
            width="100%",
            align="center",
            padding="8px 12px",
            border_bottom="1px solid var(--gray-a5)",
        ),
        # Side-by-side panels
        rx.hstack(
            _flow_panel(
                ProcessState.prev_flow_nodes,
                ProcessState.prev_flow_edges,
                ProcessState.prev_process_name,
                "Previous",
            ),
            _flow_panel(
                ProcessState.flow_nodes,
                ProcessState.flow_edges,
                ProcessState.process_name,
                "Current",
            ),
            width="100%",
            spacing="2",
            padding="8px",
        ),
        width="100%",
        border_radius="12px",
        bg="var(--gray-a2)",
        border="1px solid var(--gray-a5)",
        overflow="hidden",
    )

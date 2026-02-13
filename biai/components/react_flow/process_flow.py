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
            # Animation toggle (play/pause)
            rx.tooltip(
                rx.icon_button(
                    rx.cond(
                        ProcessState.show_animation,
                        rx.icon("pause", size=14),
                        rx.icon("play", size=14),
                    ),
                    variant="ghost",
                    size="1",
                    on_click=ProcessState.toggle_animation,
                    color=rx.cond(ProcessState.show_animation, "var(--accent-9)", "inherit"),
                ),
                content="Toggle flow animation",
            ),
            # Compare button (visible when previous process exists)
            rx.cond(
                ProcessState.has_previous_process,
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("git-compare", size=14),
                        variant="ghost",
                        size="1",
                        on_click=ProcessState.toggle_comparison,
                        color=rx.cond(ProcessState.show_comparison, "var(--accent-9)", "inherit"),
                    ),
                    content="Compare with previous process",
                ),
            ),
            rx.menu.root(
                rx.menu.trigger(
                    rx.icon_button(
                        rx.icon("download", size=14),
                        variant="ghost",
                        size="1",
                    ),
                ),
                rx.menu.content(
                    rx.menu.item(
                        "Export PNG",
                        on_click=rx.call_script("window.exportFlowToPng()"),
                    ),
                    rx.menu.item(
                        "Export SVG",
                        on_click=rx.call_script("window.exportFlowToSvg()"),
                    ),
                ),
            ),
            rx.tooltip(
                rx.icon_button(
                    rx.icon("arrow-down-up", size=14),
                    variant="ghost",
                    size="1",
                    on_click=ProcessState.toggle_layout,
                ),
                content="Toggle vertical/horizontal layout",
            ),
            # Edit mode toggle
            rx.tooltip(
                rx.icon_button(
                    rx.icon(
                        rx.cond(ProcessState.is_edit_mode, "lock-open", "pencil"),
                        size=14,
                    ),
                    variant=rx.cond(ProcessState.is_edit_mode, "soft", "ghost"),
                    size="1",
                    on_click=ProcessState.toggle_edit_mode,
                    color=rx.cond(ProcessState.is_edit_mode, "var(--accent-9)", "inherit"),
                ),
                content="Toggle edit mode",
            ),
            width="100%",
            align="center",
            padding="8px 12px",
            border_bottom="1px solid var(--gray-a5)",
        ),
        # React Flow canvas (with animation class)
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
                    nodes_connectable=ProcessState.is_edit_mode,
                    elements_selectable=ProcessState.is_edit_mode,
                    on_node_click=ProcessState.on_node_click,
                    on_node_double_click=ProcessState.on_node_double_click,
                    on_nodes_change=ProcessState.on_nodes_change,
                    on_connect=ProcessState.on_connect,
                ),
            ),
            width="100%",
            height=ProcessState.flow_height,
            border_radius="8px",
            overflow="hidden",
            class_name=ProcessState.animation_class,
        ),
        # Metrics bar
        rx.cond(
            ProcessState.has_metrics,
            rx.hstack(
                rx.cond(
                    ProcessState.bottleneck_label != "",
                    rx.hstack(
                        rx.icon("triangle-alert", size=14, color="#ef4444"),
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
        # Edit mode toolbar
        rx.cond(
            ProcessState.is_edit_mode,
            rx.hstack(
                rx.button(
                    rx.icon("plus", size=12),
                    "Add Node",
                    variant="outline",
                    size="1",
                    on_click=ProcessState.add_node("processTask"),
                ),
                rx.cond(
                    ProcessState.has_selected_node,
                    rx.fragment(
                        rx.button(
                            rx.icon("pencil", size=12),
                            "Rename",
                            variant="outline",
                            size="1",
                            on_click=ProcessState.start_edit_label,
                        ),
                        rx.button(
                            rx.icon("trash-2", size=12),
                            "Delete",
                            variant="outline",
                            size="1",
                            color_scheme="red",
                            on_click=ProcessState.delete_selected_node,
                        ),
                        # Color picker
                        rx.popover.root(
                            rx.popover.trigger(
                                rx.button(
                                    rx.icon("palette", size=12),
                                    "Color",
                                    variant="outline",
                                    size="1",
                                ),
                            ),
                            rx.popover.content(
                                rx.hstack(
                                    *[
                                        rx.box(
                                            width="24px",
                                            height="24px",
                                            border_radius="4px",
                                            bg=c,
                                            cursor="pointer",
                                            border="2px solid transparent",
                                            _hover={"border_color": "white"},
                                            on_click=ProcessState.change_node_color(c),
                                        )
                                        for c in [
                                            "#6b7280", "#22c55e", "#3b82f6", "#a855f7",
                                            "#ef4444", "#f59e0b", "#06b6d4", "#ec4899",
                                        ]
                                    ],
                                    spacing="1",
                                    flex_wrap="wrap",
                                ),
                                side="top",
                            ),
                        ),
                    ),
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("undo-2", size=12),
                    variant="ghost",
                    size="1",
                    on_click=ProcessState.undo,
                    disabled=~ProcessState.can_undo,
                ),
                rx.button(
                    rx.icon("redo-2", size=12),
                    variant="ghost",
                    size="1",
                    on_click=ProcessState.redo,
                    disabled=~ProcessState.can_redo,
                ),
                width="100%",
                padding="6px 12px",
                border_top="1px solid var(--gray-a5)",
                spacing="2",
                align="center",
                bg="var(--accent-a2)",
            ),
        ),
        # Inline label editor
        rx.cond(
            ProcessState.editing_node_id != "",
            rx.hstack(
                rx.input(
                    value=ProcessState.edit_node_label,
                    on_change=ProcessState.set_edit_node_label,
                    size="1",
                    flex="1",
                    auto_focus=True,
                ),
                rx.button("OK", size="1", on_click=ProcessState.confirm_edit_label),
                rx.button("Cancel", size="1", variant="ghost", on_click=ProcessState.cancel_edit_label),
                width="100%",
                padding="6px 12px",
                spacing="2",
                bg="var(--gray-a3)",
            ),
        ),
        # Card container styles
        width="100%",
        border_radius="12px",
        bg="var(--gray-a2)",
        border="1px solid var(--gray-a5)",
        overflow="hidden",
    )

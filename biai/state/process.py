"""Process visualization state for React Flow."""

from typing import Any

import reflex as rx


class ProcessState(rx.State):
    """Manages process flow visualization data."""

    # React Flow data (JSON-serializable)
    flow_nodes: list[dict[str, Any]] = []
    flow_edges: list[dict[str, Any]] = []
    show_process: bool = False
    process_name: str = ""
    process_type: str = ""
    total_instances: int = 0

    # Metrics
    layout_direction: str = "TB"
    bottleneck_label: str = ""
    total_transitions: int = 0

    # Node selection
    selected_node_id: str = ""
    selected_node_data: dict = {}

    # Token animation toggle
    show_animation: bool = False

    # Previous process (for comparison)
    prev_flow_nodes: list[dict[str, Any]] = []
    prev_flow_edges: list[dict[str, Any]] = []
    prev_process_name: str = ""
    show_comparison: bool = False

    # Version counter (force React re-render like ChartState)
    process_version: int = 0

    def set_process(
        self,
        nodes: list[dict],
        edges: list[dict],
        title: str = "",
        process_type: str = "",
        total_instances: int = 0,
    ):
        """Set process data (called from chat.py pipeline integration)."""
        self.flow_nodes = nodes
        self.flow_edges = edges
        self.show_process = True
        self.process_name = title
        self.process_type = process_type
        self.total_instances = total_instances
        self.process_version += 1

    def set_process_data(
        self,
        nodes: list[dict],
        edges: list[dict],
        process_name: str = "",
        process_type: str = "",
        bottleneck: str = "",
        transitions: int = 0,
        total_instances: int = 0,
    ):
        """Set process data with full metrics. Saves previous data for comparison."""
        # Copy current to previous (for comparison)
        if self.flow_nodes:
            self.prev_flow_nodes = self.flow_nodes
            self.prev_flow_edges = self.flow_edges
            self.prev_process_name = self.process_name
        self.flow_nodes = nodes
        self.flow_edges = edges
        self.show_process = True
        self.process_name = process_name
        self.process_type = process_type
        self.bottleneck_label = bottleneck
        self.total_transitions = transitions
        self.total_instances = total_instances
        self.show_comparison = False
        self.process_version += 1

    def clear_process(self):
        # Save current to prev before clearing (for comparison)
        if self.flow_nodes:
            self.prev_flow_nodes = self.flow_nodes
            self.prev_flow_edges = self.flow_edges
            self.prev_process_name = self.process_name
        self.flow_nodes = []
        self.flow_edges = []
        self.show_process = False
        self.process_name = ""
        self.process_type = ""
        self.bottleneck_label = ""
        self.total_transitions = 0
        self.total_instances = 0
        self.selected_node_id = ""
        self.selected_node_data = {}
        self.show_animation = False
        self.show_comparison = False
        self.process_version += 1

    def toggle_animation(self):
        self.show_animation = not self.show_animation

    def toggle_comparison(self):
        self.show_comparison = not self.show_comparison

    def toggle_layout(self):
        self.layout_direction = "LR" if self.layout_direction == "TB" else "TB"
        # Recalculate node positions with new direction
        if self.flow_nodes and self.flow_edges:
            from biai.ai.process_layout import calculate_layout
            self.flow_nodes = calculate_layout(
                self.flow_nodes, self.flow_edges, direction=self.layout_direction
            )
            self.process_version += 1

    def on_node_click(self, node: dict):
        self.selected_node_id = node.get("id", "")
        self.selected_node_data = node.get("data", {})

    @rx.var
    def has_previous_process(self) -> bool:
        return len(self.prev_flow_nodes) > 0

    @rx.var
    def flow_height(self) -> str:
        """Dynamic height based on node count."""
        n = len(self.flow_nodes)
        if n <= 3:
            return "250px"
        if n <= 6:
            return "350px"
        if n <= 10:
            return "420px"
        return "500px"

    @rx.var
    def animation_class(self) -> str:
        return "animated-tokens" if self.show_animation else ""

    @rx.var
    def has_metrics(self) -> bool:
        return self.bottleneck_label != "" or self.total_transitions > 0 or self.total_instances > 0

    @rx.var
    def total_transitions_display(self) -> str:
        return f"{self.total_transitions} transitions"

    @rx.var
    def total_instances_display(self) -> str:
        if self.total_instances >= 1000:
            return f"{self.total_instances / 1000:.1f}k instances"
        return f"{self.total_instances} instances"

    @rx.var
    def has_selected_node(self) -> bool:
        return self.selected_node_id != ""

    @rx.var
    def selected_node_label(self) -> str:
        return self.selected_node_data.get("label", "")

    @rx.var
    def selected_node_count(self) -> str:
        metrics = self.selected_node_data.get("metrics", {})
        cnt = metrics.get("count")
        if cnt is not None:
            return str(cnt)
        return ""

    @rx.var
    def selected_node_duration(self) -> str:
        metrics = self.selected_node_data.get("metrics", {})
        return metrics.get("avg_duration", "")

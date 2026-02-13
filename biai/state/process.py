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

    def on_node_double_click(self, node: dict):
        """Start label editing on double-click."""
        self.selected_node_id = node.get("id", "")
        self.selected_node_data = node.get("data", {})
        if self.is_edit_mode:
            self.start_edit_label()

    def on_nodes_change(self, changes: list[dict]):
        """Persist node position after drag ends."""
        for change in changes:
            if change.get("type") == "position" and not change.get("dragging", True):
                node_id = change.get("id", "")
                position = change.get("position")
                if node_id and position:
                    for i, node in enumerate(self.flow_nodes):
                        if node.get("id") == node_id:
                            updated = node.copy()
                            updated["position"] = position
                            self.flow_nodes[i] = updated
                            break

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

    # --- Edit Mode ---
    is_edit_mode: bool = False
    undo_stack: list[dict] = []  # list of {nodes, edges} snapshots
    redo_stack: list[dict] = []
    edit_node_label: str = ""
    editing_node_id: str = ""

    def toggle_edit_mode(self):
        self.is_edit_mode = not self.is_edit_mode
        if self.is_edit_mode:
            self._save_undo_snapshot()

    def _save_undo_snapshot(self):
        """Save current state to undo stack."""
        snapshot = {
            "nodes": [n.copy() for n in self.flow_nodes],
            "edges": [e.copy() for e in self.flow_edges],
        }
        self.undo_stack.append(snapshot)
        if len(self.undo_stack) > 20:
            self.undo_stack = self.undo_stack[-20:]
        self.redo_stack = []

    def undo(self):
        if not self.undo_stack:
            return
        # Save current to redo
        self.redo_stack.append({
            "nodes": [n.copy() for n in self.flow_nodes],
            "edges": [e.copy() for e in self.flow_edges],
        })
        snapshot = self.undo_stack.pop()
        self.flow_nodes = snapshot["nodes"]
        self.flow_edges = snapshot["edges"]
        self.process_version += 1

    def redo(self):
        if not self.redo_stack:
            return
        self.undo_stack.append({
            "nodes": [n.copy() for n in self.flow_nodes],
            "edges": [e.copy() for e in self.flow_edges],
        })
        snapshot = self.redo_stack.pop()
        self.flow_nodes = snapshot["nodes"]
        self.flow_edges = snapshot["edges"]
        self.process_version += 1

    def add_node(self, node_type: str = "processTask"):
        """Add a new node to the flow."""
        self._save_undo_snapshot()
        import uuid
        node_id = f"new-{uuid.uuid4().hex[:6]}"

        # Position: below existing nodes
        max_y = max((n.get("position", {}).get("y", 0) for n in self.flow_nodes), default=0)
        new_node = {
            "id": node_id,
            "type": node_type,
            "position": {"x": 200, "y": max_y + 120},
            "data": {
                "label": "New Node",
                "color": "#6b7280",
                "metrics": {},
            },
        }
        self.flow_nodes = self.flow_nodes + [new_node]
        self.process_version += 1

    def delete_selected_node(self):
        """Delete the currently selected node and its edges."""
        if not self.selected_node_id:
            return
        self._save_undo_snapshot()
        nid = self.selected_node_id
        self.flow_nodes = [n for n in self.flow_nodes if n.get("id") != nid]
        self.flow_edges = [
            e for e in self.flow_edges
            if e.get("source") != nid and e.get("target") != nid
        ]
        self.selected_node_id = ""
        self.selected_node_data = {}
        self.process_version += 1

    def start_edit_label(self):
        """Start inline editing of selected node label."""
        if self.selected_node_id:
            self.editing_node_id = self.selected_node_id
            self.edit_node_label = self.selected_node_data.get("label", "")

    def set_edit_node_label(self, value: str):
        self.edit_node_label = value

    def confirm_edit_label(self):
        """Apply edited label to the node."""
        if not self.editing_node_id:
            return
        self._save_undo_snapshot()
        for i, node in enumerate(self.flow_nodes):
            if node.get("id") == self.editing_node_id:
                updated = node.copy()
                data = updated.get("data", {}).copy()
                data["label"] = self.edit_node_label
                updated["data"] = data
                self.flow_nodes[i] = updated
                break
        self.editing_node_id = ""
        self.edit_node_label = ""
        self.process_version += 1

    def cancel_edit_label(self):
        self.editing_node_id = ""
        self.edit_node_label = ""

    def change_node_color(self, color: str):
        """Change the color of the selected node."""
        if not self.selected_node_id:
            return
        self._save_undo_snapshot()
        for i, node in enumerate(self.flow_nodes):
            if node.get("id") == self.selected_node_id:
                updated = node.copy()
                data = updated.get("data", {}).copy()
                data["color"] = color
                updated["data"] = data
                self.flow_nodes[i] = updated
                self.selected_node_data = data
                break
        self.process_version += 1

    def connect_nodes(self, source_id: str, target_id: str):
        """Add an edge between two nodes."""
        self._save_undo_snapshot()
        edge_id = f"e-{source_id}-{target_id}"
        # Avoid duplicates
        for e in self.flow_edges:
            if e.get("id") == edge_id:
                return
        new_edge = {
            "id": edge_id,
            "source": source_id,
            "target": target_id,
            "type": "smoothstep",
            "animated": True,
            "style": {"stroke": "#6b7280", "strokeWidth": 2},
        }
        self.flow_edges = self.flow_edges + [new_edge]
        self.process_version += 1

    def on_connect(self, params: dict):
        """Handle new connection from React Flow."""
        source = params.get("source", "")
        target = params.get("target", "")
        if source and target:
            self.connect_nodes(source, target)

    @rx.var
    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0

    @rx.var
    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0

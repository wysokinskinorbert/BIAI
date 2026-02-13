"""Process visualization models."""

from enum import Enum

from pydantic import BaseModel, Field

from biai.ai.dynamic_styler import DynamicStyler


class ProcessNodeType(str, Enum):
    """BPMN-inspired node types."""
    START = "start"
    END = "end"
    TASK = "task"
    GATEWAY = "gateway"
    CURRENT = "current"


class ProcessEdgeType(str, Enum):
    """Edge visual types."""
    NORMAL = "normal"
    ANIMATED = "animated"
    DIMMED = "dimmed"


class ProcessNode(BaseModel):
    """Single node in process flow."""
    id: str
    label: str
    node_type: ProcessNodeType = ProcessNodeType.TASK
    count: int | None = None
    avg_duration_min: float | None = None
    is_bottleneck: bool = False
    metadata: dict = Field(default_factory=dict)


class ProcessEdge(BaseModel):
    """Edge connecting two nodes."""
    id: str
    source: str
    target: str
    edge_type: ProcessEdgeType = ProcessEdgeType.NORMAL
    label: str = ""
    count: int | None = None


class ProcessFlowConfig(BaseModel):
    """Complete process flow configuration for React Flow."""
    nodes: list[ProcessNode] = Field(default_factory=list)
    edges: list[ProcessEdge] = Field(default_factory=list)
    title: str = ""
    process_type: str = ""
    total_instances: int = 0
    layout_direction: str = "TB"

    def to_react_flow_data(self) -> tuple[list[dict], list[dict]]:
        """Convert to React Flow nodes/edges format for frontend."""
        rf_nodes = []
        y_spacing = 100
        x_spacing = 250

        for i, node in enumerate(self.nodes):
            if self.layout_direction == "TB":
                x, y = 0, i * y_spacing
            else:
                x, y = i * x_spacing, 0

            # Build metrics dict matching JS node expectations
            metrics: dict = {}
            if node.count is not None:
                metrics["count"] = node.count
            if node.avg_duration_min is not None:
                metrics["avg_duration"] = _format_duration(node.avg_duration_min)
            if node.is_bottleneck:
                metrics["is_bottleneck"] = True
                metrics["bottleneck_duration"] = _format_duration(
                    node.avg_duration_min
                ) if node.avg_duration_min else ""

            color = DynamicStyler.get_color(node.id, node.metadata.get("ai_color"))
            icon = DynamicStyler.get_icon(node.id, node.metadata.get("ai_icon"))

            data = {
                "label": node.label,
                "nodeType": node.node_type.value,
                "color": color,
                "icon": icon,
                "metrics": metrics,
            }
            data.update(node.metadata)

            rf_node: dict = {
                "id": node.id,
                "type": _get_react_flow_node_type(node.node_type),
                "position": {"x": x, "y": y},
                "data": data,
            }
            if node.is_bottleneck:
                rf_node["className"] = "bottleneck"
            rf_nodes.append(rf_node)

        rf_edges = []
        for edge in self.edges:
            rf_edges.append({
                "id": edge.id,
                "source": edge.source,
                "target": edge.target,
                "label": edge.label,
                "animated": edge.edge_type == ProcessEdgeType.ANIMATED,
                "style": _get_edge_style(edge.edge_type),
                "type": "smoothstep",
            })

        return rf_nodes, rf_edges


def _get_react_flow_node_type(node_type: ProcessNodeType) -> str:
    """Map internal type to React Flow custom node type."""
    return {
        ProcessNodeType.START: "processStart",
        ProcessNodeType.END: "processEnd",
        ProcessNodeType.TASK: "processTask",
        ProcessNodeType.GATEWAY: "processGateway",
        ProcessNodeType.CURRENT: "processCurrent",
    }.get(node_type, "processTask")


def _get_edge_style(edge_type: ProcessEdgeType) -> dict:
    """Get CSS style for edge type."""
    return {
        ProcessEdgeType.NORMAL: {"stroke": "#555", "strokeWidth": 2},
        ProcessEdgeType.ANIMATED: {"stroke": "#8b5cf6", "strokeWidth": 2},
        ProcessEdgeType.DIMMED: {"stroke": "#333", "strokeWidth": 1, "strokeDasharray": "5,5"},
    }.get(edge_type, {"stroke": "#555"})


def _format_duration(minutes: float | None) -> str:
    """Format duration in minutes to human-readable string."""
    if minutes is None:
        return ""
    if minutes < 60:
        return f"{minutes:.0f}m"
    elif minutes < 1440:
        return f"{minutes / 60:.1f}h"
    else:
        return f"{minutes / 1440:.1f}d"

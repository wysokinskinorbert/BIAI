"""Tests for process visualization module."""
import pandas as pd
import pytest

from biai.models.process import (
    ProcessFlowConfig, ProcessNode, ProcessEdge, ProcessNodeType, ProcessEdgeType,
)
from biai.ai.process_detector import ProcessDetector
from biai.ai.process_graph_builder import ProcessGraphBuilder
from biai.ai.process_layout import calculate_layout


# ──────────────── ProcessDetector Tests ────────────────

class TestProcessDetector:

    def setup_method(self):
        self.detector = ProcessDetector()

    def test_detect_transition_columns(self):
        df = pd.DataFrame({
            'from_status': ['a', 'b'], 'to_status': ['b', 'c'],
            'count': [10, 5],
        })
        assert self.detector.detect_in_dataframe(df, "process")

    def test_detect_status_plus_metric(self):
        df = pd.DataFrame({
            'stage': ['lead', 'qualified', 'proposal'],
            'count': [300, 200, 100],
        })
        assert self.detector.detect_in_dataframe(df, "lejek")

    def test_reject_empty_dataframe(self):
        df = pd.DataFrame()
        assert not self.detector.detect_in_dataframe(df, "process")

    def test_reject_single_row(self):
        df = pd.DataFrame({'status': ['a'], 'count': [1]})
        assert not self.detector.detect_in_dataframe(df, "process")

    def test_is_process_question_polish(self):
        assert self.detector.is_process_question("Pokaż proces realizacji zamówień")

    def test_is_process_question_english(self):
        assert self.detector.is_process_question("Show me the workflow")

    def test_not_process_question(self):
        assert not self.detector.is_process_question("Ile kosztuje produkt X?")

    def test_detect_process_type_order(self):
        df = pd.DataFrame({'a': [1]})
        assert self.detector.detect_process_type(df, "SELECT * FROM ORDER_PROCESS_LOG") == "order_fulfillment"

    def test_detect_process_type_pipeline(self):
        df = pd.DataFrame({'a': [1]})
        assert self.detector.detect_process_type(df, "SELECT * FROM SALES_PIPELINE") == "sales_pipeline"

    def test_detect_process_type_ticket(self):
        df = pd.DataFrame({'a': [1]})
        assert self.detector.detect_process_type(df, "SELECT * FROM SUPPORT_TICKETS") == "support_ticket"

    def test_detect_process_type_approval(self):
        df = pd.DataFrame({'a': [1]})
        assert self.detector.detect_process_type(df, "SELECT * FROM APPROVAL_REQUESTS") == "approval_workflow"

    def test_detect_process_type_generic(self):
        df = pd.DataFrame({'a': [1]})
        assert self.detector.detect_process_type(df, "SELECT * FROM SOME_TABLE") == "generic"


# ──────────────── ProcessGraphBuilder Tests ────────────────

class TestProcessGraphBuilder:

    def setup_method(self):
        self.builder = ProcessGraphBuilder()

    def test_build_from_transitions(self):
        df = pd.DataFrame({
            'from_status': ['a', 'b', 'c'],
            'to_status': ['b', 'c', 'd'],
            'transition_count': [100, 90, 80],
        })
        config = self.builder.build(df, "order_fulfillment", "test")
        assert config is not None
        assert len(config.nodes) >= 3
        assert len(config.edges) >= 3

    def test_build_from_aggregates(self):
        df = pd.DataFrame({
            'stage': ['lead', 'qualified', 'proposal', 'closed_won'],
            'count': [300, 200, 100, 30],
        })
        config = self.builder.build(df, "sales_pipeline", "lejek")
        assert config is not None
        assert len(config.nodes) >= 4

    def test_build_from_known_sequence(self):
        df = pd.DataFrame({'x': [1, 2, 3]})
        config = self.builder.build(df, "approval_workflow", "test")
        assert config is not None
        ids = [n.id for n in config.nodes]
        assert "draft" in ids
        assert "executed" in ids

    def test_unknown_type_returns_none(self):
        df = pd.DataFrame({'x': [1, 2, 3]})
        config = self.builder.build(df, "unknown_type", "test")
        assert config is None

    def test_bottleneck_detection(self):
        df = pd.DataFrame({
            'from_status': ['a', 'b'],
            'to_status': ['b', 'c'],
            'transition_count': [100, 90],
            'avg_duration_minutes': [10, 500],
        })
        config = self.builder.build(df, "order_fulfillment", "test")
        bottlenecks = [n for n in config.nodes if n.is_bottleneck]
        assert len(bottlenecks) >= 1

    def test_to_react_flow_data_format(self):
        df = pd.DataFrame({
            'from_status': ['a', 'b'],
            'to_status': ['b', 'c'],
            'transition_count': [100, 90],
        })
        config = self.builder.build(df, "order_fulfillment", "test")
        rf_nodes, rf_edges = config.to_react_flow_data()
        for n in rf_nodes:
            assert "id" in n
            assert "position" in n
            assert "data" in n
            assert "type" in n
        for e in rf_edges:
            assert "source" in e
            assert "target" in e
            assert "type" in e

    def test_known_branches_added(self):
        df = pd.DataFrame({
            'stage': ['lead', 'qualified', 'proposal', 'negotiation', 'closed_won'],
            'count': [300, 200, 100, 60, 30],
        })
        config = self.builder.build(df, "sales_pipeline", "lejek")
        ids = [n.id for n in config.nodes]
        assert "closed_lost" in ids


# ──────────────── Process Layout Tests ────────────────

class TestProcessLayout:

    def test_linear_layout_tb(self):
        nodes = [{"id": "a", "position": {}}, {"id": "b", "position": {}}, {"id": "c", "position": {}}]
        edges = [{"source": "a", "target": "b"}, {"source": "b", "target": "c"}]
        result = calculate_layout(nodes, edges, "TB")
        y = [n["position"]["y"] for n in result]
        assert y[0] < y[1] < y[2]

    def test_linear_layout_lr(self):
        nodes = [{"id": "a", "position": {}}, {"id": "b", "position": {}}, {"id": "c", "position": {}}]
        edges = [{"source": "a", "target": "b"}, {"source": "b", "target": "c"}]
        result = calculate_layout(nodes, edges, "LR")
        x = [n["position"]["x"] for n in result]
        assert x[0] < x[1] < x[2]

    def test_branching_layout(self):
        nodes = [
            {"id": "s", "position": {}}, {"id": "g", "position": {}},
            {"id": "l", "position": {}}, {"id": "r", "position": {}},
            {"id": "e", "position": {}},
        ]
        edges = [
            {"source": "s", "target": "g"},
            {"source": "g", "target": "l"}, {"source": "g", "target": "r"},
            {"source": "l", "target": "e"}, {"source": "r", "target": "e"},
        ]
        result = calculate_layout(nodes, edges, "TB")
        pos = {n["id"]: n["position"] for n in result}
        assert pos["l"]["y"] == pos["r"]["y"]
        assert pos["l"]["x"] != pos["r"]["x"]
        assert pos["s"]["y"] < pos["g"]["y"] < pos["l"]["y"] < pos["e"]["y"]


# ──────────────── Models Tests ────────────────

class TestProcessModels:

    def test_process_node_defaults(self):
        node = ProcessNode(id="test", label="Test")
        assert node.node_type == ProcessNodeType.TASK
        assert node.is_bottleneck is False
        assert node.count is None

    def test_process_edge_defaults(self):
        edge = ProcessEdge(id="e1", source="a", target="b")
        assert edge.edge_type == ProcessEdgeType.NORMAL
        assert edge.label == ""

    def test_flow_config_to_react_flow(self):
        config = ProcessFlowConfig(
            nodes=[ProcessNode(id="a", label="A", node_type=ProcessNodeType.START)],
            edges=[ProcessEdge(id="e1", source="a", target="b")],
        )
        rf_nodes, rf_edges = config.to_react_flow_data()
        assert rf_nodes[0]["type"] == "processStart"
        assert rf_edges[0]["type"] == "smoothstep"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

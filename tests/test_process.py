"""Tests for process detection and graph building."""

import pytest
import pandas as pd

from biai.ai.dynamic_styler import DynamicStyler
from biai.ai.process_detector import ProcessDetector
from biai.ai.process_graph_builder import ProcessGraphBuilder
from biai.models.discovery import DiscoveredProcess
from biai.models.process import (
    ProcessFlowConfig,
    ProcessNodeType,
    ProcessEdgeType,
    _format_duration,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def detector():
    return ProcessDetector()


@pytest.fixture
def builder():
    return ProcessGraphBuilder()


@pytest.fixture
def transition_df():
    """Order fulfillment transition log data."""
    return pd.DataFrame({
        "from_status": [
            None, "order_placed", "payment_pending", "payment_confirmed",
            "warehouse_assigned", "picking", "packing", "shipped", "in_transit",
        ],
        "to_status": [
            "order_placed", "payment_pending", "payment_confirmed",
            "warehouse_assigned", "picking", "packing", "shipped",
            "in_transit", "delivered",
        ],
        "transition_count": [100, 100, 98, 98, 95, 95, 90, 88, 85],
        "avg_duration_minutes": [1, 30, 15, 60, 45, 240, 20, 2160, 10],
    })


@pytest.fixture
def aggregate_df():
    """Sales pipeline aggregate data."""
    return pd.DataFrame({
        "stage": ["lead", "qualified", "proposal", "negotiation", "closed_won"],
        "deal_count": [100, 75, 50, 30, 20],
        "avg_deal_value": [15000, 25000, 40000, 60000, 80000],
    })


@pytest.fixture
def support_transition_df():
    """Support ticket transition data."""
    return pd.DataFrame({
        "from_status": [None, "new", "assigned", "investigating", "in_progress"],
        "to_status": ["new", "assigned", "investigating", "in_progress", "resolved"],
        "count": [250, 248, 245, 200, 180],
    })


@pytest.fixture
def nan_transition_df():
    """Transition data with NaN values that should be filtered."""
    return pd.DataFrame({
        "from_status": [None, "A", "B", float("nan"), "C"],
        "to_status": ["A", "B", "C", float("nan"), "D"],
        "count": [10, 8, 7, 5, 4],
    })


@pytest.fixture
def order_discovery():
    """DiscoveredProcess for order fulfillment."""
    return DiscoveredProcess(
        id="order_fulfillment",
        name="Order Fulfillment",
        tables=["order_fulfillment", "order_process_log"],
        stages=[
            "order_placed", "payment_pending", "payment_confirmed",
            "warehouse_assigned", "picking", "packing",
            "shipped", "in_transit", "delivered",
        ],
        confidence=0.9,
    )


@pytest.fixture
def sales_discovery():
    """DiscoveredProcess for sales pipeline."""
    return DiscoveredProcess(
        id="sales_pipeline",
        name="Sales Pipeline",
        stages=["lead", "qualified", "proposal", "negotiation", "closed_won"],
        branches={"negotiation": ["closed_won", "closed_lost"]},
        confidence=0.85,
    )


# ---------------------------------------------------------------------------
# ProcessDetector tests
# ---------------------------------------------------------------------------

class TestProcessDetector:
    """Test process detection heuristics."""

    def test_detect_transition_columns(self, detector, transition_df):
        assert detector.detect_in_dataframe(transition_df, "show order process flow")

    def test_detect_aggregate_columns(self, detector, aggregate_df):
        assert detector.detect_in_dataframe(aggregate_df, "show sales pipeline stages")

    def test_detect_by_question_keywords(self, detector):
        df = pd.DataFrame({
            "status": ["new", "in_progress", "done", "pending", "cancelled"],
            "name": ["a", "b", "c", "d", "e"],
            "value": [1, 2, 3, 4, 5],
        })
        assert detector.detect_in_dataframe(df, "show the process flow for orders")

    def test_no_detect_plain_data(self, detector):
        df = pd.DataFrame({
            "name": ["Alice", "Bob"],
            "revenue": [1000, 2000],
        })
        assert not detector.detect_in_dataframe(df, "show top customers by revenue")

    def test_no_detect_empty_df(self, detector):
        df = pd.DataFrame()
        assert not detector.detect_in_dataframe(df, "show process")

    def test_no_detect_single_row(self, detector):
        df = pd.DataFrame({"status": ["done"], "count": [5]})
        assert not detector.detect_in_dataframe(df, "show workflow stages")

    def test_detect_process_type_order(self, detector, transition_df):
        sql = "SELECT * FROM order_process_log"
        assert detector.detect_process_type(transition_df, sql) == "order_fulfillment"

    def test_detect_process_type_pipeline(self, detector, aggregate_df):
        sql = "SELECT * FROM pipeline_history"
        assert detector.detect_process_type(aggregate_df, sql) == "sales_pipeline"

    def test_detect_process_type_support(self, detector, support_transition_df):
        sql = "SELECT * FROM ticket_history"
        assert detector.detect_process_type(support_transition_df, sql) == "support_ticket"

    def test_detect_process_type_approval(self, detector):
        df = pd.DataFrame({"step_name": ["draft", "submitted"], "count": [10, 8]})
        sql = "SELECT * FROM approval_steps"
        assert detector.detect_process_type(df, sql) == "approval_workflow"

    def test_detect_process_type_unknown(self, detector, transition_df):
        sql = "SELECT * FROM some_table"
        result = detector.detect_process_type(transition_df, sql)
        assert result in ("order_fulfillment", "unknown", "", "generic")

    def test_detect_dynamic_match(self, detector, transition_df, order_discovery):
        """Dynamic detection matches by table name."""
        sql = "SELECT * FROM order_fulfillment"
        process_type, discovered = detector.detect_process_type_dynamic(
            transition_df, sql, [order_discovery],
        )
        assert process_type == "order_fulfillment"
        assert discovered is not None

    def test_detect_dynamic_no_match_fallback(self, detector, transition_df):
        """Dynamic detection falls back to legacy when no match."""
        sql = "SELECT * FROM random_table"
        procs = [DiscoveredProcess(id="unrelated", name="X", tables=["other_table"])]
        process_type, discovered = detector.detect_process_type_dynamic(
            transition_df, sql, procs,
        )
        # Falls back to legacy (which checks for order_process in SQL)
        assert discovered is None


# ---------------------------------------------------------------------------
# ProcessGraphBuilder tests
# ---------------------------------------------------------------------------

class TestProcessGraphBuilder:
    """Test graph building strategies."""

    def test_build_from_transitions(self, builder, transition_df):
        config = builder.build(transition_df, "order_fulfillment", "Order process flow")
        assert config is not None
        assert isinstance(config, ProcessFlowConfig)
        assert len(config.nodes) > 0
        assert len(config.edges) > 0

    def test_build_from_transitions_with_discovery(self, builder, transition_df, order_discovery):
        config = builder.build(
            transition_df, "order_fulfillment", "Order process flow",
            discovered=order_discovery,
        )
        assert config is not None
        # Nodes should be ordered according to discovered stages
        node_ids = [n.id for n in config.nodes]
        assert node_ids[0] in order_discovery.stages

    def test_transitions_no_nan_nodes(self, builder, nan_transition_df):
        config = builder.build(nan_transition_df, "unknown", "Test nan filtering")
        assert config is not None
        node_ids = {n.id for n in config.nodes}
        assert "nan" not in node_ids
        assert "None" not in node_ids

    def test_transitions_unique_edges(self, builder, transition_df):
        config = builder.build(transition_df, "order_fulfillment", "Test unique edges")
        assert config is not None
        edge_ids = [e.id for e in config.edges]
        assert len(edge_ids) == len(set(edge_ids)), "Duplicate edge IDs found"

    def test_transitions_bottleneck_detection(self, builder, transition_df):
        config = builder.build(transition_df, "order_fulfillment", "Bottleneck test")
        assert config is not None
        bottleneck_nodes = [n for n in config.nodes if n.is_bottleneck]
        assert len(bottleneck_nodes) <= 1  # at most one bottleneck

    def test_build_from_aggregates(self, builder, aggregate_df):
        config = builder.build(aggregate_df, "sales_pipeline", "Sales pipeline funnel")
        assert config is not None
        assert len(config.nodes) >= 5
        assert len(config.edges) >= 4

    def test_aggregates_with_discovery_branches(self, builder, sales_discovery):
        df = pd.DataFrame({
            "stage": ["lead", "qualified", "proposal", "negotiation", "closed_won"],
            "deal_count": [100, 75, 50, 30, 20],
        })
        config = builder.build(
            df, "sales_pipeline", "Pipeline with branches",
            discovered=sales_discovery,
        )
        assert config is not None
        node_ids = {n.id for n in config.nodes}
        # closed_lost should be added from branches
        assert "closed_lost" in node_ids

    def test_build_from_discovery(self, builder, order_discovery):
        """Strategy 3: build from discovered stages when data doesn't match other patterns."""
        df = pd.DataFrame({"x": [1, 2, 3]})  # doesn't match transition or aggregate
        config = builder.build(
            df, "order_fulfillment", "Discovery test",
            discovered=order_discovery,
        )
        assert config is not None
        assert len(config.nodes) == 9  # 9 stages in order_fulfillment

    def test_build_unknown_type_no_match(self, builder):
        df = pd.DataFrame({"x": [1, 2, 3]})
        config = builder.build(df, "unknown_type", "No match test")
        assert config is None

    def test_node_types_start_end(self, builder, transition_df):
        config = builder.build(transition_df, "order_fulfillment", "Node types test")
        assert config is not None
        start_nodes = [n for n in config.nodes if n.node_type == ProcessNodeType.START]
        end_nodes = [n for n in config.nodes if n.node_type == ProcessNodeType.END]
        assert len(start_nodes) == 1
        assert len(end_nodes) == 1

    def test_to_react_flow_data(self, builder, transition_df):
        config = builder.build(transition_df, "order_fulfillment", "React flow test")
        assert config is not None
        rf_nodes, rf_edges = config.to_react_flow_data()
        assert len(rf_nodes) > 0
        assert len(rf_edges) > 0
        # Check node structure
        for node in rf_nodes:
            assert "id" in node
            assert "type" in node
            assert "position" in node
            assert "data" in node
            assert "label" in node["data"]
            assert "color" in node["data"]
            assert "icon" in node["data"]
        # Check edge structure
        for edge in rf_edges:
            assert "id" in edge
            assert "source" in edge
            assert "target" in edge

    def test_react_flow_bottleneck_classname(self, builder, transition_df):
        config = builder.build(transition_df, "order_fulfillment", "Bottleneck class test")
        assert config is not None
        rf_nodes, _ = config.to_react_flow_data()
        bottleneck_nodes = [n for n in rf_nodes if n.get("className") == "bottleneck"]
        assert len(bottleneck_nodes) <= 1


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestProcessModels:
    """Test process data models and helpers."""

    def test_format_duration_minutes(self):
        assert _format_duration(30) == "30m"
        assert _format_duration(0) == "0m"

    def test_format_duration_hours(self):
        assert _format_duration(90) == "1.5h"
        assert _format_duration(120) == "2.0h"

    def test_format_duration_days(self):
        assert _format_duration(1440) == "1.0d"
        assert _format_duration(2880) == "2.0d"

    def test_format_duration_none(self):
        assert _format_duration(None) == ""

    def test_dynamic_styler_covers_all_known_statuses(self):
        """DynamicStyler should provide non-default colors for all process statuses."""
        known_states = [
            "order_placed", "payment_pending", "payment_confirmed",
            "warehouse_assigned", "picking", "packing", "shipped",
            "in_transit", "delivered",
            "lead", "qualified", "proposal", "negotiation",
            "closed_won", "closed_lost",
            "new", "assigned", "investigating", "waiting_customer",
            "in_progress", "resolved", "closed", "reopened",
            "draft", "submitted", "level1_review", "level2_review",
            "approved", "rejected", "executed",
        ]
        for status in known_states:
            color = DynamicStyler.get_color(status)
            assert color.startswith("#"), f"No color for {status}"
            icon = DynamicStyler.get_icon(status)
            assert icon != "circle", f"No icon for {status}"

    def test_edge_types(self):
        assert ProcessEdgeType.ANIMATED.value == "animated"
        assert ProcessEdgeType.DIMMED.value == "dimmed"
        assert ProcessEdgeType.NORMAL.value == "normal"

    def test_node_types(self):
        assert ProcessNodeType.START.value == "start"
        assert ProcessNodeType.END.value == "end"
        assert ProcessNodeType.TASK.value == "task"
        assert ProcessNodeType.GATEWAY.value == "gateway"
        assert ProcessNodeType.CURRENT.value == "current"


# ---------------------------------------------------------------------------
# Layout tests
# ---------------------------------------------------------------------------

class TestProcessLayout:
    """Test layout calculation."""

    def test_order_states_with_discovery(self, builder, order_discovery):
        """States should be ordered according to discovered stages."""
        states = {"delivered", "order_placed", "shipped", "picking"}
        ordered = builder._order_states(states, order_discovery)
        # Check relative ordering matches discovery stages
        disc_stages = order_discovery.stages
        for i, s in enumerate(ordered):
            if s in disc_stages:
                idx = disc_stages.index(s)
                for j in range(i + 1, len(ordered)):
                    if ordered[j] in disc_stages:
                        assert disc_stages.index(ordered[j]) > idx

    def test_order_states_no_discovery_unknown(self, builder):
        """Unknown states all score 0.5 so they sort alphabetically among themselves."""
        states = {"C", "A", "B"}
        ordered = builder._order_states(states, None)
        assert ordered == ["A", "B", "C"]

    def test_order_states_heuristic_lifecycle(self, builder):
        """Lifecycle stages should be ordered logically, not alphabetically."""
        states = {"completed", "active", "pending", "cancelled", "draft"}
        ordered = builder._order_states(states, None)
        # draft (0.02) < pending (0.10) < active (0.40) < completed (0.90) < cancelled (0.94)
        assert ordered == ["draft", "pending", "active", "completed", "cancelled"]

    def test_order_states_heuristic_hr(self, builder):
        """HR employment statuses should follow logical order."""
        states = {"terminated", "active", "on_leave", "probation"}
        ordered = builder._order_states(states, None)
        # probation (0.28) < active (0.40) < on_leave (0.55) < terminated (0.94)
        assert ordered == ["probation", "active", "on_leave", "terminated"]

    def test_order_states_heuristic_orders(self, builder):
        """Order processing statuses: start → middle → end."""
        states = {"delivered", "draft", "shipped", "confirmed", "cancelled"}
        ordered = builder._order_states(states, None)
        # draft (0.02) < confirmed (0.25) < shipped (0.44) < delivered (0.88) < cancelled (0.94)
        assert ordered == ["draft", "confirmed", "shipped", "delivered", "cancelled"]

    def test_order_states_extra_states(self, builder, order_discovery):
        states = {"order_placed", "delivered", "extra_state"}
        ordered = builder._order_states(states, order_discovery)
        assert "extra_state" in ordered
        assert ordered[-1] == "extra_state"  # extra goes at end

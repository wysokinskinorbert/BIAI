"""Tests for EventLog model and EventLogBuilder."""

import pytest
from datetime import datetime, timedelta

from biai.models.event_log import EventLog, EventRecord
from biai.models.discovery import (
    DiscoveredProcess,
    TransitionPattern,
    ColumnCandidate,
    EntityChain,
    Evidence,
)
from biai.ai.process_graph_builder import ProcessGraphBuilder


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def order_event_log():
    """Event log with order fulfillment transitions."""
    base = datetime(2026, 1, 1, 10, 0, 0)
    events = [
        # Case 1: happy path
        EventRecord(case_id="ORD-001", activity="placed", timestamp=base),
        EventRecord(case_id="ORD-001", activity="paid", timestamp=base + timedelta(hours=1)),
        EventRecord(case_id="ORD-001", activity="shipped", timestamp=base + timedelta(hours=24)),
        EventRecord(case_id="ORD-001", activity="delivered", timestamp=base + timedelta(hours=72)),
        # Case 2: happy path
        EventRecord(case_id="ORD-002", activity="placed", timestamp=base + timedelta(minutes=30)),
        EventRecord(case_id="ORD-002", activity="paid", timestamp=base + timedelta(hours=2)),
        EventRecord(case_id="ORD-002", activity="shipped", timestamp=base + timedelta(hours=48)),
        EventRecord(case_id="ORD-002", activity="delivered", timestamp=base + timedelta(hours=96)),
        # Case 3: cancelled path
        EventRecord(case_id="ORD-003", activity="placed", timestamp=base + timedelta(hours=3)),
        EventRecord(case_id="ORD-003", activity="cancelled", timestamp=base + timedelta(hours=5)),
    ]
    return EventLog(
        process_id="order_fulfillment",
        events=events,
        case_count=3,
        activity_count=5,
    )


@pytest.fixture
def no_timestamp_log():
    """Event log without timestamps."""
    events = [
        EventRecord(case_id="T-1", activity="new"),
        EventRecord(case_id="T-1", activity="assigned"),
        EventRecord(case_id="T-1", activity="resolved"),
        EventRecord(case_id="T-2", activity="new"),
        EventRecord(case_id="T-2", activity="assigned"),
        EventRecord(case_id="T-2", activity="closed"),
    ]
    return EventLog(process_id="tickets", events=events, case_count=2, activity_count=4)


# ---------------------------------------------------------------------------
# EventLog model tests
# ---------------------------------------------------------------------------

class TestEventLog:

    def test_transition_matrix(self, order_event_log):
        matrix = order_event_log.get_transition_matrix()
        # placed → paid: 2 cases
        assert matrix[("placed", "paid")] == 2
        # paid → shipped: 2 cases
        assert matrix[("paid", "shipped")] == 2
        # shipped → delivered: 2 cases
        assert matrix[("shipped", "delivered")] == 2
        # placed → cancelled: 1 case
        assert matrix[("placed", "cancelled")] == 1

    def test_variant_distribution(self, order_event_log):
        variants = order_event_log.get_variant_distribution()
        assert len(variants) >= 2
        # Happy path (placed→paid→shipped→delivered) should be most common
        top_variant, top_count = variants[0]
        assert top_count == 2
        assert top_variant == ["placed", "paid", "shipped", "delivered"]
        # Cancelled variant
        cancelled_variant = [v for v, c in variants if "cancelled" in v]
        assert len(cancelled_variant) == 1

    def test_activity_durations(self, order_event_log):
        durations = order_event_log.get_activity_durations()
        assert "placed" in durations
        assert "paid" in durations
        # placed → paid takes 1-2 hours = 3600-7200 seconds
        assert 0 < durations["placed"] < 10800

    def test_get_activities(self, order_event_log):
        activities = order_event_log.get_activities()
        assert activities[0] == "placed"  # first in order of appearance
        assert "delivered" in activities
        assert "cancelled" in activities

    def test_transition_matrix_no_timestamps(self, no_timestamp_log):
        """Transition matrix should work even without timestamps."""
        matrix = no_timestamp_log.get_transition_matrix()
        # Events ordered by datetime.min (insertion order preserved)
        assert ("new", "assigned") in matrix
        assert matrix[("new", "assigned")] == 2

    def test_empty_log(self):
        log = EventLog(process_id="empty", events=[])
        assert log.get_transition_matrix() == {}
        assert log.get_variant_distribution() == []
        assert log.get_activity_durations() == {}
        assert log.get_activities() == []

    def test_single_event_per_case(self):
        events = [
            EventRecord(case_id="1", activity="done"),
            EventRecord(case_id="2", activity="done"),
        ]
        log = EventLog(process_id="test", events=events)
        # No transitions possible with single events
        assert log.get_transition_matrix() == {}
        # Each case has one variant ["done"]
        variants = log.get_variant_distribution()
        assert len(variants) == 1
        assert variants[0] == (["done"], 2)


# ---------------------------------------------------------------------------
# ProcessGraphBuilder with EventLog
# ---------------------------------------------------------------------------

class TestProcessGraphBuilderWithEventLog:

    def test_build_from_event_log(self, order_event_log):
        import pandas as pd
        builder = ProcessGraphBuilder()
        df = pd.DataFrame({"x": [1]})  # dummy df
        config = builder.build(
            df, "order_fulfillment", "Show order flow",
            event_log=order_event_log,
        )
        assert config is not None
        node_ids = {n.id for n in config.nodes}
        assert "placed" in node_ids
        assert "delivered" in node_ids
        assert "cancelled" in node_ids

    def test_event_log_edge_labels_are_counts(self, order_event_log):
        import pandas as pd
        builder = ProcessGraphBuilder()
        df = pd.DataFrame({"x": [1]})
        config = builder.build(
            df, "order_fulfillment", "Show order flow",
            event_log=order_event_log,
        )
        assert config is not None
        # Find edge placed→paid
        edge = next((e for e in config.edges if e.source == "placed" and e.target == "paid"), None)
        assert edge is not None
        assert edge.label == "2"  # 2 cases

    def test_event_log_start_end_nodes(self, order_event_log):
        import pandas as pd
        from biai.models.process import ProcessNodeType
        builder = ProcessGraphBuilder()
        df = pd.DataFrame({"x": [1]})
        config = builder.build(
            df, "order_fulfillment", "Show order flow",
            event_log=order_event_log,
        )
        assert config is not None
        start_nodes = [n for n in config.nodes if n.node_type == ProcessNodeType.START]
        end_nodes = [n for n in config.nodes if n.node_type == ProcessNodeType.END]
        # "placed" should be START (only source, never target in some transitions)
        # Actually placed appears as source but also... let me think
        # placed → paid (source), placed → cancelled (source)
        # Nothing → placed (no transition starts with something going to placed)
        # So placed is a start node
        assert any(n.id == "placed" for n in start_nodes)

    def test_event_log_priority_over_transitions(self, order_event_log):
        """Event log strategy should take priority over transition columns."""
        import pandas as pd
        builder = ProcessGraphBuilder()
        # DataFrame has transition columns, but event_log is provided
        df = pd.DataFrame({
            "from_status": ["a", "b"],
            "to_status": ["b", "c"],
            "count": [10, 5],
        })
        config = builder.build(
            df, "order_fulfillment", "Show order flow",
            event_log=order_event_log,
        )
        assert config is not None
        # Should use event log activities, not df columns
        node_ids = {n.id for n in config.nodes}
        assert "placed" in node_ids  # from event log
        assert "a" not in node_ids  # not from df

    def test_empty_event_log_falls_through(self):
        """Empty event log should fall through to other strategies."""
        import pandas as pd
        builder = ProcessGraphBuilder()
        empty_log = EventLog(process_id="test", events=[])
        df = pd.DataFrame({
            "from_status": ["a", "b"],
            "to_status": ["b", "c"],
            "count": [10, 5],
        })
        config = builder.build(
            df, "unknown", "Test",
            event_log=empty_log,
        )
        # Falls through to transition strategy
        assert config is not None
        node_ids = {n.id for n in config.nodes}
        assert "a" in node_ids

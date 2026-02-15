"""Tests for ECharts Sankey and Timeline built from EventLog."""

import pytest
from datetime import datetime, timedelta

from biai.models.event_log import EventLog, EventRecord
from biai.ai.echarts_builder import (
    build_sankey_from_event_log,
    build_timeline_from_event_log,
    _build_sankey,
    can_use_echarts,
)
from biai.models.chart import ChartConfig, ChartType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def order_event_log():
    """Event log with order fulfillment transitions."""
    base = datetime(2026, 1, 1, 10, 0, 0)
    events = [
        EventRecord(case_id="ORD-001", activity="placed", timestamp=base),
        EventRecord(case_id="ORD-001", activity="paid", timestamp=base + timedelta(hours=1)),
        EventRecord(case_id="ORD-001", activity="shipped", timestamp=base + timedelta(hours=24)),
        EventRecord(case_id="ORD-001", activity="delivered", timestamp=base + timedelta(hours=72)),
        EventRecord(case_id="ORD-002", activity="placed", timestamp=base + timedelta(minutes=30)),
        EventRecord(case_id="ORD-002", activity="paid", timestamp=base + timedelta(hours=2)),
        EventRecord(case_id="ORD-002", activity="shipped", timestamp=base + timedelta(hours=48)),
        EventRecord(case_id="ORD-002", activity="delivered", timestamp=base + timedelta(hours=96)),
        EventRecord(case_id="ORD-003", activity="placed", timestamp=base + timedelta(hours=3)),
        EventRecord(case_id="ORD-003", activity="cancelled", timestamp=base + timedelta(hours=5)),
    ]
    return EventLog(process_id="order_fulfillment", events=events, case_count=3, activity_count=5)


@pytest.fixture
def no_timestamp_log():
    """Event log without timestamps."""
    events = [
        EventRecord(case_id="T-1", activity="new"),
        EventRecord(case_id="T-1", activity="assigned"),
        EventRecord(case_id="T-1", activity="resolved"),
    ]
    return EventLog(process_id="tickets", events=events, case_count=1, activity_count=3)


# ---------------------------------------------------------------------------
# Sankey tests
# ---------------------------------------------------------------------------

class TestSankeyFromEventLog:

    def test_sankey_has_nodes_and_links(self, order_event_log):
        option = build_sankey_from_event_log(order_event_log)
        assert option
        series = option["series"][0]
        assert series["type"] == "sankey"
        nodes = {n["name"] for n in series["data"]}
        assert "placed" in nodes
        assert "delivered" in nodes
        assert "cancelled" in nodes

    def test_sankey_link_values_match_transitions(self, order_event_log):
        option = build_sankey_from_event_log(order_event_log)
        links = option["series"][0]["links"]
        placed_paid = next(l for l in links if l["source"] == "placed" and l["target"] == "paid")
        assert placed_paid["value"] == 2

    def test_sankey_empty_log_returns_empty(self):
        empty = EventLog(process_id="x", events=[])
        assert build_sankey_from_event_log(empty) == {}

    def test_sankey_single_case_no_transitions(self):
        events = [EventRecord(case_id="1", activity="done")]
        log = EventLog(process_id="x", events=events)
        assert build_sankey_from_event_log(log) == {}

    def test_sankey_custom_title(self, order_event_log):
        option = build_sankey_from_event_log(order_event_log, title="My Flow")
        assert option["title"]["text"] == "My Flow"

    def test_can_use_echarts_sankey(self):
        assert can_use_echarts(ChartType.SANKEY)


class TestSankeyFromDataFrame:

    def test_build_from_df_with_source_target(self):
        import pandas as pd
        df = pd.DataFrame({
            "source": ["A", "A", "B"],
            "target": ["B", "C", "C"],
            "value": [10, 5, 3],
        })
        config = ChartConfig(chart_type=ChartType.SANKEY, title="Test")
        from biai.ai.echarts_builder import build_echarts_option
        option = build_echarts_option(config, df)
        assert option
        assert option["series"][0]["type"] == "sankey"
        assert len(option["series"][0]["links"]) == 3


# ---------------------------------------------------------------------------
# Timeline tests
# ---------------------------------------------------------------------------

class TestTimelineFromEventLog:

    def test_timeline_has_scatter_series(self, order_event_log):
        option = build_timeline_from_event_log(order_event_log)
        assert option
        assert option["series"][0]["type"] == "scatter"
        assert option["xAxis"]["type"] == "time"

    def test_timeline_y_axis_has_activities(self, order_event_log):
        option = build_timeline_from_event_log(order_event_log)
        y_data = option["yAxis"]["data"]
        assert "placed" in y_data
        assert "delivered" in y_data

    def test_timeline_data_points_count(self, order_event_log):
        option = build_timeline_from_event_log(order_event_log)
        data = option["series"][0]["data"]
        assert len(data) == 10  # 10 events with timestamps

    def test_timeline_no_timestamps_returns_empty(self, no_timestamp_log):
        assert build_timeline_from_event_log(no_timestamp_log) == {}

    def test_timeline_empty_log_returns_empty(self):
        empty = EventLog(process_id="x", events=[])
        assert build_timeline_from_event_log(empty) == {}

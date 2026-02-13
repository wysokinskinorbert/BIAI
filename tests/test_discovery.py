"""Tests for dynamic process discovery and DynamicStyler."""

import pytest

from biai.ai.dynamic_styler import DynamicStyler
from biai.ai.process_cache import ProcessDiscoveryCache
from biai.models.connection import ConnectionConfig, DBType
from biai.models.discovery import (
    ColumnCandidate,
    DiscoveredProcess,
    EntityChain,
    TransitionPattern,
)


# ---------------------------------------------------------------------------
# DynamicStyler tests
# ---------------------------------------------------------------------------

class TestDynamicStyler:
    """Test algorithmic color and icon assignment."""

    def test_semantic_color_success(self):
        assert DynamicStyler.get_color("delivered") == "#22c55e"
        assert DynamicStyler.get_color("completed") == "#22c55e"
        assert DynamicStyler.get_color("approved") == "#22c55e"
        assert DynamicStyler.get_color("closed_won") == "#22c55e"

    def test_semantic_color_error(self):
        assert DynamicStyler.get_color("rejected") == "#ef4444"
        assert DynamicStyler.get_color("cancelled") == "#ef4444"
        assert DynamicStyler.get_color("closed_lost") == "#ef4444"

    def test_semantic_color_warning(self):
        assert DynamicStyler.get_color("pending") == "#eab308"
        assert DynamicStyler.get_color("waiting_customer") == "#eab308"
        assert DynamicStyler.get_color("payment_pending") == "#eab308"

    def test_semantic_color_info(self):
        assert DynamicStyler.get_color("in_progress") == "#3b82f6"
        assert DynamicStyler.get_color("in_transit") == "#3b82f6"
        assert DynamicStyler.get_color("picking") == "#3b82f6"
        assert DynamicStyler.get_color("packing") == "#3b82f6"

    def test_semantic_color_review(self):
        assert DynamicStyler.get_color("level1_review") == "#a855f7"
        assert DynamicStyler.get_color("level2_review") == "#a855f7"
        assert DynamicStyler.get_color("negotiation") == "#a855f7"
        assert DynamicStyler.get_color("proposal") == "#a855f7"

    def test_semantic_color_start(self):
        assert DynamicStyler.get_color("new") == "#6366f1"
        assert DynamicStyler.get_color("draft") == "#6366f1"
        assert DynamicStyler.get_color("order_placed") == "#6366f1"
        assert DynamicStyler.get_color("lead") == "#6366f1"
        assert DynamicStyler.get_color("submitted") == "#6366f1"

    def test_semantic_color_transition(self):
        assert DynamicStyler.get_color("shipped") == "#0ea5e9"

    def test_semantic_color_reopen(self):
        assert DynamicStyler.get_color("reopened") == "#f97316"

    def test_ai_suggestion_priority(self):
        """AI suggestion overrides semantic matching."""
        assert DynamicStyler.get_color("delivered", "#ff0000") == "#ff0000"
        assert DynamicStyler.get_color("unknown_status", "#aabbcc") == "#aabbcc"

    def test_ai_suggestion_invalid_ignored(self):
        """Non-hex AI suggestion is ignored."""
        result = DynamicStyler.get_color("delivered", "not-a-color")
        assert result == "#22c55e"  # falls through to semantic

    def test_hash_determinism(self):
        """Same unknown status always produces same color."""
        color1 = DynamicStyler.get_color("xqz_nomatch_789")
        color2 = DynamicStyler.get_color("xqz_nomatch_789")
        assert color1 == color2
        assert color1 in DynamicStyler.PALETTE

    def test_hash_different_statuses_can_differ(self):
        """Different statuses might get different colors."""
        c1 = DynamicStyler.get_color("aaa_status")
        c2 = DynamicStyler.get_color("zzz_status")
        # They *can* be the same by hash collision, but the hash is deterministic
        assert c1 in DynamicStyler.PALETTE
        assert c2 in DynamicStyler.PALETTE

    def test_partial_match(self):
        """Status containing a keyword gets matched."""
        assert DynamicStyler.get_color("my_custom_pending_status") == "#eab308"

    # --- Icons ---

    def test_semantic_icon_direct(self):
        assert DynamicStyler.get_icon("shipped") == "truck"
        assert DynamicStyler.get_icon("delivered") == "package-check"
        assert DynamicStyler.get_icon("new") == "plus-circle"
        assert DynamicStyler.get_icon("approved") == "thumbs-up"
        assert DynamicStyler.get_icon("rejected") == "thumbs-down"

    def test_icon_ai_suggestion_priority(self):
        assert DynamicStyler.get_icon("shipped", "rocket") == "rocket"

    def test_icon_default_fallback(self):
        assert DynamicStyler.get_icon("xyz_totally_unknown") == "circle"

    def test_icon_partial_match(self):
        """Longest keyword match wins: 'pending' (7) vs 'review' (6) -> 'pending' wins."""
        assert DynamicStyler.get_icon("is_pending_status") == "clock"

    def test_known_statuses_have_colors(self):
        """All statuses from the old hardcoded dict should still get meaningful colors."""
        old_statuses = [
            "delivered", "closed", "closed_won", "approved", "executed", "resolved",
            "closed_lost", "rejected", "cancelled", "waiting_customer", "payment_pending",
            "pending", "in_progress", "in_transit", "investigating", "picking", "packing",
            "level1_review", "level2_review", "negotiation", "proposal", "order_placed",
            "payment_confirmed", "warehouse_assigned", "shipped", "lead", "qualified",
            "new", "assigned", "draft", "submitted", "reopened",
        ]
        for status in old_statuses:
            color = DynamicStyler.get_color(status)
            assert color.startswith("#"), f"No color for {status}"
            assert color != DynamicStyler.DEFAULT_COLOR or status == "unknown", (
                f"Status {status} got default color"
            )

    def test_known_statuses_have_icons(self):
        """All statuses from the old hardcoded dict should still get meaningful icons."""
        old_statuses = [
            "order_placed", "payment_pending", "payment_confirmed", "warehouse_assigned",
            "picking", "packing", "shipped", "in_transit", "delivered",
            "lead", "qualified", "proposal", "negotiation", "closed_won", "closed_lost",
            "new", "assigned", "investigating", "waiting_customer", "in_progress",
            "resolved", "closed", "reopened", "draft", "submitted",
            "level1_review", "level2_review", "approved", "rejected", "executed",
        ]
        for status in old_statuses:
            icon = DynamicStyler.get_icon(status)
            assert icon != "circle", f"Status {status} got default icon 'circle'"


# ---------------------------------------------------------------------------
# Discovery models tests
# ---------------------------------------------------------------------------

class TestDiscoveryModels:
    """Test Pydantic discovery models."""

    def test_column_candidate(self):
        cc = ColumnCandidate(
            table_name="orders", column_name="status", role="status",
            distinct_values=["new", "done"], cardinality=2, confidence=0.8,
        )
        assert cc.table_name == "orders"
        assert cc.cardinality == 2

    def test_transition_pattern(self):
        tp = TransitionPattern(
            table_name="order_log",
            from_column="from_status",
            to_column="to_status",
        )
        assert tp.transitions == []

    def test_entity_chain(self):
        ec = EntityChain(
            tables=["order_log", "orders"],
            join_keys=[("order_id", "order_id")],
            entity_name="order",
        )
        assert len(ec.tables) == 2

    def test_discovered_process(self):
        dp = DiscoveredProcess(
            id="order_process",
            name="Order Process",
            stages=["new", "processing", "done"],
            stage_counts={"new": 10, "processing": 5, "done": 20},
            confidence=0.8,
        )
        assert dp.get_label("new") == "New"
        assert dp.get_label("processing") == "Processing"

    def test_discovered_process_ai_labels(self):
        dp = DiscoveredProcess(
            id="test",
            name="Test",
            ai_labels={"new": "Brand New"},
        )
        assert dp.get_label("new") == "Brand New"
        assert dp.get_label("unknown") == "Unknown"

    def test_serialization_roundtrip(self):
        dp = DiscoveredProcess(
            id="test",
            name="Test Process",
            stages=["a", "b", "c"],
            confidence=0.75,
            ai_colors={"a": "#ff0000"},
        )
        data = dp.to_serializable()
        restored = DiscoveredProcess.from_serializable(data)
        assert restored.id == "test"
        assert restored.stages == ["a", "b", "c"]
        assert restored.ai_colors == {"a": "#ff0000"}

    def test_get_stage_color_icon(self):
        dp = DiscoveredProcess(
            id="test",
            name="Test",
            ai_colors={"a": "#123456"},
            ai_icons={"a": "star"},
        )
        assert dp.get_stage_color("a") == "#123456"
        assert dp.get_stage_color("b") is None
        assert dp.get_stage_icon("a") == "star"
        assert dp.get_stage_icon("b") is None


# ---------------------------------------------------------------------------
# ProcessDiscoveryCache tests
# ---------------------------------------------------------------------------

class TestProcessDiscoveryCache:
    """Test TTL-based cache."""

    @pytest.fixture
    def config(self):
        return ConnectionConfig(
            db_type=DBType.POSTGRESQL,
            host="localhost",
            port=5433,
            database="test_db",
        )

    @pytest.fixture
    def cache(self):
        return ProcessDiscoveryCache(ttl=60)

    def test_store_and_get(self, cache, config):
        procs = [DiscoveredProcess(id="p1", name="Process 1")]
        cache.store(config, procs)
        result = cache.get(config)
        assert result is not None
        assert len(result) == 1
        assert result[0].id == "p1"

    def test_get_miss(self, cache, config):
        assert cache.get(config) is None

    def test_invalidate(self, cache, config):
        procs = [DiscoveredProcess(id="p1", name="Process 1")]
        cache.store(config, procs)
        cache.invalidate(config)
        assert cache.get(config) is None

    def test_clear(self, cache, config):
        procs = [DiscoveredProcess(id="p1", name="Process 1")]
        cache.store(config, procs)
        cache.clear()
        assert cache.get(config) is None

    def test_ttl_expiry(self, config):
        import time
        cache = ProcessDiscoveryCache(ttl=0)  # immediate expiry
        procs = [DiscoveredProcess(id="p1", name="Process 1")]
        cache.store(config, procs)
        time.sleep(0.01)
        assert cache.get(config) is None

    def test_different_configs(self, cache):
        cfg1 = ConnectionConfig(db_type=DBType.POSTGRESQL, host="h1", port=5432, database="d1")
        cfg2 = ConnectionConfig(db_type=DBType.ORACLE, host="h2", port=1521, database="d2")
        cache.store(cfg1, [DiscoveredProcess(id="p1", name="P1")])
        cache.store(cfg2, [DiscoveredProcess(id="p2", name="P2")])
        assert cache.get(cfg1)[0].id == "p1"
        assert cache.get(cfg2)[0].id == "p2"

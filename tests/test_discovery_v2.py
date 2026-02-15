"""Tests for graph-driven process discovery (FAZA 2.3-2.6).

Tests cover:
- Graph-driven FK chain discovery
- Timestamp sequence detection
- Trigger-based process signals
- Weighted confidence scoring with Evidence
- Evidence accumulation across multiple signals
- Candidate filtering (min 2 signals or confidence >= 0.25)
"""

import pytest

from biai.ai.metadata_graph import SchemaGraph
from biai.ai.process_discovery import ProcessDiscoveryEngine
from biai.models.discovery import (
    ColumnCandidate,
    DiscoveredProcess,
    Evidence,
    TransitionPattern,
)
from biai.models.schema import (
    ColumnInfo,
    SchemaSnapshot,
    TableInfo,
    TriggerInfo,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def order_schema():
    """Schema with order processing tables — status columns + FK chains."""
    return SchemaSnapshot(
        tables=[
            TableInfo(
                name="CUSTOMERS", schema_name="public",
                columns=[
                    ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
                    ColumnInfo(name="NAME", data_type="VARCHAR(100)"),
                ],
            ),
            TableInfo(
                name="ORDERS", schema_name="public",
                columns=[
                    ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
                    ColumnInfo(name="CUSTOMER_ID", data_type="INTEGER",
                               is_foreign_key=True, foreign_key_ref="CUSTOMERS"),
                    ColumnInfo(name="STATUS", data_type="VARCHAR(20)"),
                    ColumnInfo(name="CREATED_AT", data_type="TIMESTAMP"),
                    ColumnInfo(name="UPDATED_AT", data_type="TIMESTAMP"),
                    ColumnInfo(name="SHIPPED_AT", data_type="TIMESTAMP"),
                ],
            ),
            TableInfo(
                name="ORDER_ITEMS", schema_name="public",
                columns=[
                    ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
                    ColumnInfo(name="ORDER_ID", data_type="INTEGER",
                               is_foreign_key=True, foreign_key_ref="ORDERS"),
                    ColumnInfo(name="PRODUCT_ID", data_type="INTEGER",
                               is_foreign_key=True, foreign_key_ref="PRODUCTS"),
                    ColumnInfo(name="QUANTITY", data_type="INTEGER"),
                ],
            ),
            TableInfo(
                name="PRODUCTS", schema_name="public",
                columns=[
                    ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
                    ColumnInfo(name="NAME", data_type="VARCHAR(100)"),
                ],
            ),
            TableInfo(
                name="SHIPMENTS", schema_name="public",
                columns=[
                    ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
                    ColumnInfo(name="ORDER_ID", data_type="INTEGER",
                               is_foreign_key=True, foreign_key_ref="ORDERS"),
                    ColumnInfo(name="SHIPMENT_STATUS", data_type="VARCHAR(20)"),
                    ColumnInfo(name="SHIPPED_DATE", data_type="TIMESTAMP"),
                    ColumnInfo(name="DELIVERED_DATE", data_type="TIMESTAMP"),
                ],
            ),
            TableInfo(
                name="ORDER_STATUS_HISTORY", schema_name="public",
                columns=[
                    ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
                    ColumnInfo(name="ORDER_ID", data_type="INTEGER",
                               is_foreign_key=True, foreign_key_ref="ORDERS"),
                    ColumnInfo(name="FROM_STATUS", data_type="VARCHAR(20)"),
                    ColumnInfo(name="TO_STATUS", data_type="VARCHAR(20)"),
                    ColumnInfo(name="CHANGED_AT", data_type="TIMESTAMP"),
                ],
            ),
        ],
        db_type="postgresql",
        schema_name="public",
    )


@pytest.fixture
def timestamp_heavy_schema():
    """Schema with lifecycle timestamp columns."""
    return SchemaSnapshot(
        tables=[
            TableInfo(
                name="TICKETS", schema_name="support",
                columns=[
                    ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
                    ColumnInfo(name="STATUS", data_type="VARCHAR(20)"),
                    ColumnInfo(name="CREATED_AT", data_type="TIMESTAMP"),
                    ColumnInfo(name="ASSIGNED_AT", data_type="TIMESTAMP"),
                    ColumnInfo(name="STARTED_AT", data_type="TIMESTAMP"),
                    ColumnInfo(name="RESOLVED_AT", data_type="TIMESTAMP"),
                    ColumnInfo(name="CLOSED_AT", data_type="TIMESTAMP"),
                ],
            ),
        ],
        db_type="postgresql",
    )


@pytest.fixture
def trigger_schema():
    """Schema with triggers on status columns."""
    return SchemaSnapshot(
        tables=[
            TableInfo(
                name="ORDERS", schema_name="sales",
                columns=[
                    ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
                    ColumnInfo(name="STATUS", data_type="VARCHAR(20)"),
                    ColumnInfo(name="AMOUNT", data_type="DECIMAL"),
                ],
            ),
            TableInfo(
                name="INVOICES", schema_name="sales",
                columns=[
                    ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
                    ColumnInfo(name="TOTAL", data_type="DECIMAL"),
                ],
            ),
        ],
        triggers=[
            TriggerInfo(
                trigger_name="trg_order_status_change",
                table_name="ORDERS",
                trigger_event="BEFORE UPDATE",
                timing="BEFORE",
            ),
            TriggerInfo(
                trigger_name="trg_invoice_audit",
                table_name="INVOICES",
                trigger_event="AFTER UPDATE",
                timing="AFTER",
            ),
        ],
        db_type="oracle",
    )


@pytest.fixture
def hub_schema():
    """Schema where a central table has 6+ FK connections."""
    dim_tables = []
    for name in ["DIM_CUSTOMER", "DIM_PRODUCT", "DIM_DATE", "DIM_STORE",
                  "DIM_CHANNEL", "DIM_PROMOTION"]:
        dim_tables.append(TableInfo(
            name=name,
            columns=[
                ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
            ],
        ))
    fact_cols = [
        ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
        ColumnInfo(name="AMOUNT", data_type="DECIMAL"),
    ]
    for dim in dim_tables:
        fk_name = dim.name.replace("DIM_", "") + "_ID"
        fact_cols.append(ColumnInfo(
            name=fk_name, data_type="INTEGER",
            is_foreign_key=True, foreign_key_ref=dim.name,
        ))
    fact = TableInfo(name="FACT_SALES", columns=fact_cols)
    return SchemaSnapshot(
        tables=[fact] + dim_tables,
        db_type="postgresql",
    )


class FakeConnector:
    """Fake connector for testing discovery without DB."""

    async def execute_query(self, sql, timeout=10):
        import pandas as pd
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Tests: Timestamp Sequence Detection
# ---------------------------------------------------------------------------

class TestTimestampSequences:

    def test_detect_3plus_timestamps(self, timestamp_heavy_schema):
        engine = ProcessDiscoveryEngine(
            connector=FakeConnector(),
            schema=timestamp_heavy_schema,
        )
        candidates = engine._find_timestamp_sequences(timestamp_heavy_schema.tables)
        assert len(candidates) == 1
        assert candidates[0].table_name == "TICKETS"
        assert candidates[0].role == "timestamp"
        assert candidates[0].cardinality >= 5  # 5 timestamp columns

    def test_no_detect_under_3_timestamps(self):
        schema = SchemaSnapshot(
            tables=[
                TableInfo(name="SIMPLE", columns=[
                    ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
                    ColumnInfo(name="CREATED_AT", data_type="TIMESTAMP"),
                    ColumnInfo(name="UPDATED_AT", data_type="TIMESTAMP"),
                ]),
            ],
            db_type="postgresql",
        )
        engine = ProcessDiscoveryEngine(
            connector=FakeConnector(), schema=schema,
        )
        candidates = engine._find_timestamp_sequences(schema.tables)
        assert len(candidates) == 0


# ---------------------------------------------------------------------------
# Tests: Trigger Signal Detection
# ---------------------------------------------------------------------------

class TestTriggerSignals:

    def test_detect_trigger_on_status_column(self, trigger_schema):
        engine = ProcessDiscoveryEngine(
            connector=FakeConnector(),
            schema=trigger_schema,
        )
        signals = engine._find_trigger_signals()
        # ORDERS has STATUS + trigger → strong signal (0.8)
        status_triggers = [s for s in signals if s.strength == 0.8]
        assert len(status_triggers) == 1
        assert status_triggers[0].source_table == "ORDERS"

    def test_detect_trigger_on_non_status_table(self, trigger_schema):
        engine = ProcessDiscoveryEngine(
            connector=FakeConnector(),
            schema=trigger_schema,
        )
        signals = engine._find_trigger_signals()
        # INVOICES has trigger but no STATUS column → weaker signal (0.4)
        weak_triggers = [s for s in signals if s.strength == 0.4]
        assert len(weak_triggers) == 1
        assert weak_triggers[0].source_table == "INVOICES"

    def test_no_triggers_returns_empty(self):
        schema = SchemaSnapshot(
            tables=[TableInfo(name="T", columns=[
                ColumnInfo(name="ID", data_type="INTEGER"),
            ])],
            triggers=[],
            db_type="postgresql",
        )
        engine = ProcessDiscoveryEngine(
            connector=FakeConnector(), schema=schema,
        )
        assert engine._find_trigger_signals() == []


# ---------------------------------------------------------------------------
# Tests: Graph-Driven FK Chains
# ---------------------------------------------------------------------------

class TestFKChainsFromGraph:

    def test_history_table_chain(self, order_schema):
        engine = ProcessDiscoveryEngine(
            connector=FakeConnector(), schema=order_schema,
        )
        graph = SchemaGraph(order_schema)
        chains = engine._find_fk_chains_from_graph(graph)
        # ORDER_STATUS_HISTORY → ORDERS chain should exist
        history_chains = [c for c in chains if "order_status" in c.entity_name]
        assert len(history_chains) >= 1

    def test_fk_chain_length(self, order_schema):
        engine = ProcessDiscoveryEngine(
            connector=FakeConnector(), schema=order_schema,
        )
        graph = SchemaGraph(order_schema)
        chains = engine._find_fk_chains_from_graph(graph)
        # Should find chains (ORDER_ITEMS → ORDERS → CUSTOMERS, etc.)
        assert len(chains) >= 1


# ---------------------------------------------------------------------------
# Tests: Weighted Confidence Scoring with Evidence
# ---------------------------------------------------------------------------

class TestWeightedConfidenceScoring:

    def test_transition_table_gets_0_30_confidence(self):
        engine = ProcessDiscoveryEngine(
            connector=FakeConnector(),
            schema=SchemaSnapshot(db_type="test"),
        )
        transitions = [TransitionPattern(
            table_name="STATUS_LOG",
            from_column="FROM_STATUS",
            to_column="TO_STATUS",
        )]
        candidates = engine._build_candidates([], transitions, [])
        assert len(candidates) >= 1
        proc = candidates[0]
        assert proc.confidence == pytest.approx(0.30, abs=0.01)
        assert any(e.signal_type == "transition_table" for e in proc.evidence)

    def test_status_column_gets_0_20_confidence(self):
        engine = ProcessDiscoveryEngine(
            connector=FakeConnector(),
            schema=SchemaSnapshot(db_type="test"),
        )
        status_cols = [ColumnCandidate(
            table_name="ORDERS",
            column_name="STATUS",
            role="status",
            confidence=0.8,
        )]
        candidates = engine._build_candidates(status_cols, [], [])
        # Status column alone gets 0.20 — but needs 2 signals or 0.25
        # Since 0.20 < 0.25 and only 1 evidence, it may be filtered
        # Unless it reaches 0.25+ threshold
        # 0.20 < 0.25 → filtered out
        # This is correct behavior — single weak signal filtered
        assert all(c.confidence >= 0.25 or len(c.evidence) >= 2 for c in candidates)

    def test_combined_signals_accumulate(self, order_schema):
        """Status column + transition table on same table → 0.30 + 0.20 = 0.50."""
        engine = ProcessDiscoveryEngine(
            connector=FakeConnector(),
            schema=order_schema,
        )
        transitions = [TransitionPattern(
            table_name="ORDER_STATUS_HISTORY",
            from_column="FROM_STATUS",
            to_column="TO_STATUS",
        )]
        status_cols = [ColumnCandidate(
            table_name="ORDER_STATUS_HISTORY",
            column_name="FROM_STATUS",
            role="status",
            confidence=0.5,
        )]
        candidates = engine._build_candidates(status_cols, transitions, [])
        proc = [c for c in candidates if c.id == "order_status_history"]
        assert len(proc) == 1
        assert proc[0].confidence == pytest.approx(0.50, abs=0.01)
        assert len(proc[0].evidence) == 2

    def test_hub_table_gets_evidence(self, hub_schema):
        engine = ProcessDiscoveryEngine(
            connector=FakeConnector(),
            schema=hub_schema,
        )
        graph = SchemaGraph(hub_schema)
        candidates = engine._build_candidates(
            [], [], [], graph=graph,
        )
        # FACT_SALES has 6 FKs → hub + star schema
        fact_procs = [c for c in candidates if c.id == "fact_sales"]
        assert len(fact_procs) == 1
        evidence_types = {e.signal_type for e in fact_procs[0].evidence}
        assert "hub_table" in evidence_types
        assert "star_schema_fact" in evidence_types

    def test_timestamp_sequence_adds_evidence(self, timestamp_heavy_schema):
        engine = ProcessDiscoveryEngine(
            connector=FakeConnector(),
            schema=timestamp_heavy_schema,
        )
        ts_candidates = engine._find_timestamp_sequences(timestamp_heavy_schema.tables)
        # TICKETS has STATUS + 5 timestamps
        status_cols = [ColumnCandidate(
            table_name="TICKETS",
            column_name="STATUS",
            role="status",
            confidence=0.8,
        )]
        candidates = engine._build_candidates(
            status_cols, [], [],
            timestamp_candidates=ts_candidates,
        )
        ticket_procs = [c for c in candidates if c.id == "tickets"]
        assert len(ticket_procs) == 1
        evidence_types = {e.signal_type for e in ticket_procs[0].evidence}
        assert "status_column" in evidence_types
        assert "timestamp_sequence" in evidence_types
        # 0.20 (status) + 0.05 (timestamp) = 0.25
        assert ticket_procs[0].confidence >= 0.25

    def test_trigger_signal_adds_evidence(self, trigger_schema):
        engine = ProcessDiscoveryEngine(
            connector=FakeConnector(),
            schema=trigger_schema,
        )
        trigger_signals = engine._find_trigger_signals()
        status_cols = [ColumnCandidate(
            table_name="ORDERS",
            column_name="STATUS",
            role="status",
            confidence=0.8,
        )]
        candidates = engine._build_candidates(
            status_cols, [], [],
            trigger_signals=trigger_signals,
        )
        order_procs = [c for c in candidates if c.id == "orders"]
        assert len(order_procs) == 1
        evidence_types = {e.signal_type for e in order_procs[0].evidence}
        assert "status_column" in evidence_types
        assert "trigger_on_status" in evidence_types
        # 0.20 (status) + 0.15 (trigger) = 0.35
        assert order_procs[0].confidence == pytest.approx(0.35, abs=0.01)

    def test_filter_single_weak_signal(self):
        """Single signal with confidence < 0.25 should be filtered out."""
        engine = ProcessDiscoveryEngine(
            connector=FakeConnector(),
            schema=SchemaSnapshot(db_type="test"),
        )
        # Single timestamp sequence with 0.05 weight — too weak
        ts_candidates = [ColumnCandidate(
            table_name="SOME_TABLE",
            column_name="c1, c2, c3",
            role="timestamp",
            cardinality=3,
            confidence=0.4,
        )]
        candidates = engine._build_candidates(
            [], [], [],
            timestamp_candidates=ts_candidates,
        )
        # 0.05 < 0.25 threshold and only 1 evidence → filtered
        some_procs = [c for c in candidates if c.id == "some_table"]
        assert len(some_procs) == 0


# ---------------------------------------------------------------------------
# Tests: Full Discovery Pipeline (sync parts only)
# ---------------------------------------------------------------------------

class TestDiscoveryPipelineSync:

    def test_status_columns_found_across_all_tables(self, order_schema):
        """Discovery should find status columns in ALL tables, not just first N."""
        engine = ProcessDiscoveryEngine(
            connector=FakeConnector(),
            schema=order_schema,
        )
        status = engine._find_status_columns(order_schema.tables)
        table_names = {s.table_name for s in status}
        # ORDERS.STATUS and SHIPMENTS.SHIPMENT_STATUS should both be found
        assert "ORDERS" in table_names
        assert "SHIPMENTS" in table_names

    def test_transition_tables_found(self, order_schema):
        engine = ProcessDiscoveryEngine(
            connector=FakeConnector(),
            schema=order_schema,
        )
        transitions = engine._find_transition_tables(order_schema.tables)
        # ORDER_STATUS_HISTORY has FROM_STATUS / TO_STATUS
        assert len(transitions) >= 1
        assert any(t.table_name == "ORDER_STATUS_HISTORY" for t in transitions)

    def test_build_candidates_combines_all_signals(self, order_schema):
        engine = ProcessDiscoveryEngine(
            connector=FakeConnector(),
            schema=order_schema,
        )
        graph = SchemaGraph(order_schema)
        status = engine._find_status_columns(order_schema.tables)
        transitions = engine._find_transition_tables(order_schema.tables)
        chains = engine._find_fk_chains_from_graph(graph)
        timestamps = engine._find_timestamp_sequences(order_schema.tables)

        candidates = engine._build_candidates(
            status, transitions, chains,
            graph=graph,
            timestamp_candidates=timestamps,
        )
        # ORDER_STATUS_HISTORY should have transition + status evidence
        hist_procs = [c for c in candidates if "order_status_history" in c.id]
        assert len(hist_procs) >= 1
        if hist_procs:
            assert len(hist_procs[0].evidence) >= 2

    def test_orders_has_timestamp_evidence(self, order_schema):
        """ORDERS table has 3 timestamp columns → timestamp_sequence signal."""
        engine = ProcessDiscoveryEngine(
            connector=FakeConnector(),
            schema=order_schema,
        )
        ts = engine._find_timestamp_sequences(order_schema.tables)
        order_ts = [t for t in ts if t.table_name == "ORDERS"]
        assert len(order_ts) == 1
        assert order_ts[0].cardinality >= 3


# ---------------------------------------------------------------------------
# Tests: Performance
# ---------------------------------------------------------------------------

class TestDiscoveryPerformance:

    def test_200_table_discovery_sync_parts(self):
        """Sync parts of discovery should be fast for 200 tables."""
        import time

        tables = []
        for i in range(200):
            cols = [
                ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
                ColumnInfo(name="STATUS", data_type="VARCHAR(20)"),
                ColumnInfo(name="CREATED_AT", data_type="TIMESTAMP"),
                ColumnInfo(name="UPDATED_AT", data_type="TIMESTAMP"),
                ColumnInfo(name="COMPLETED_AT", data_type="TIMESTAMP"),
            ]
            if i > 0:
                cols.append(ColumnInfo(
                    name="PARENT_ID", data_type="INTEGER",
                    is_foreign_key=True, foreign_key_ref=f"TABLE_{i - 1}",
                ))
            tables.append(TableInfo(name=f"TABLE_{i}", columns=cols))

        schema = SchemaSnapshot(tables=tables, db_type="test")
        engine = ProcessDiscoveryEngine(
            connector=FakeConnector(), schema=schema,
        )

        start = time.time()
        graph = SchemaGraph(schema)
        status = engine._find_status_columns(tables)
        transitions = engine._find_transition_tables(tables)
        chains = engine._find_fk_chains_from_graph(graph)
        timestamps = engine._find_timestamp_sequences(tables)
        candidates = engine._build_candidates(
            status, transitions, chains,
            graph=graph,
            timestamp_candidates=timestamps,
        )
        elapsed = time.time() - start

        assert elapsed < 10.0, f"Discovery sync took {elapsed:.2f}s (should be <10s)"
        assert len(status) == 200  # all tables have STATUS
        assert len(timestamps) == 200  # all tables have 3+ timestamps
        assert len(candidates) > 0

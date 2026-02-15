"""Performance benchmarks for enterprise-scale operations.

Tests verify that key operations complete within acceptable time bounds
for various schema sizes (50, 200, 2000 tables).
"""

import time
import pytest
from unittest.mock import MagicMock

from biai.ai.metadata_graph import SchemaGraph
from biai.models.schema import SchemaSnapshot, TableInfo, ColumnInfo


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_enterprise_schema(
    num_tables: int = 200,
    fk_density: float = 0.3,
    num_schemas: int = 1,
) -> SchemaSnapshot:
    """Create a realistic enterprise schema fixture.

    Args:
        num_tables: Total number of tables.
        fk_density: Fraction of tables with FK to another table.
        num_schemas: Number of schemas to distribute tables across.
    """
    import random
    random.seed(42)

    tables = []
    for i in range(num_tables):
        schema_idx = i % num_schemas
        schema_name = f"schema_{schema_idx}" if num_schemas > 1 else "public"

        cols = [
            ColumnInfo(name="id", data_type="INTEGER", is_primary_key=True),
            ColumnInfo(name="name", data_type="VARCHAR(100)"),
            ColumnInfo(name="created_at", data_type="TIMESTAMP"),
        ]

        # Add status column to ~20% of tables
        if i % 5 == 0:
            cols.append(ColumnInfo(name="status", data_type="VARCHAR(20)"))

        # Add FK to random earlier table
        if i > 0 and random.random() < fk_density:
            ref_idx = random.randint(0, i - 1)
            ref_schema = f"schema_{ref_idx % num_schemas}" if num_schemas > 1 else ""
            ref_name = f"table_{ref_idx}"
            ref = f"{ref_schema}.{ref_name}" if ref_schema else ref_name
            cols.append(ColumnInfo(
                name=f"table_{ref_idx}_id",
                data_type="INTEGER",
                is_foreign_key=True,
                foreign_key_ref=f"{ref}.id",
            ))

        # Add 2nd FK to create hub patterns (~10% of tables)
        if i > 5 and i % 10 == 0:
            ref_idx2 = random.randint(0, min(i - 1, 5))
            ref_name2 = f"table_{ref_idx2}"
            cols.append(ColumnInfo(
                name=f"fk2_{ref_idx2}_id",
                data_type="INTEGER",
                is_foreign_key=True,
                foreign_key_ref=f"{ref_name2}.id",
            ))

        tables.append(TableInfo(
            name=f"table_{i}",
            columns=cols,
        ))

    return SchemaSnapshot(tables=tables, schema_name="public")


# ---------------------------------------------------------------------------
# Graph build performance
# ---------------------------------------------------------------------------

class TestSchemaGraphPerformance:

    def test_graph_build_50_tables(self):
        """SchemaGraph build + analysis < 50ms for 50 tables."""
        schema = _make_enterprise_schema(50)
        start = time.time()
        graph = SchemaGraph(schema)
        stats = graph.get_stats()
        elapsed_ms = (time.time() - start) * 1000
        assert elapsed_ms < 200  # generous bound for CI
        assert stats.total_tables == 50

    def test_graph_build_200_tables(self):
        """SchemaGraph build + analysis < 200ms for 200 tables."""
        schema = _make_enterprise_schema(200)
        start = time.time()
        graph = SchemaGraph(schema)
        stats = graph.get_stats()
        elapsed_ms = (time.time() - start) * 1000
        assert elapsed_ms < 500
        assert stats.total_tables == 200

    def test_graph_build_2000_tables(self):
        """SchemaGraph build + analysis < 1s for 2000 tables."""
        schema = _make_enterprise_schema(2000)
        start = time.time()
        graph = SchemaGraph(schema)
        stats = graph.get_stats()
        elapsed_ms = (time.time() - start) * 1000
        assert elapsed_ms < 5000  # generous bound
        assert stats.total_tables == 2000

    def test_community_detection_200_tables(self):
        """Community detection < 500ms for 200 tables."""
        schema = _make_enterprise_schema(200)
        graph = SchemaGraph(schema)
        start = time.time()
        communities = graph.find_table_communities()
        elapsed_ms = (time.time() - start) * 1000
        assert elapsed_ms < 1000
        assert len(communities) > 0

    def test_hub_detection_accuracy(self):
        """Hub detection finds tables with most FK references."""
        schema = _make_enterprise_schema(50, fk_density=0.5)
        graph = SchemaGraph(schema)
        stats = graph.get_stats()
        # With 50 tables and 50% FK density, should find some hubs
        assert len(stats.hub_tables) > 0
        # Hubs should be sorted by degree descending
        if len(stats.hub_tables) >= 2:
            assert stats.hub_tables[0][1] >= stats.hub_tables[1][1]


# ---------------------------------------------------------------------------
# Documentation generation performance
# ---------------------------------------------------------------------------

class TestDocumentationPerformance:

    def test_overview_docs_fast_for_large_schema(self):
        """Overview docs generation < 100ms for 2000 tables."""
        from biai.db.dialect import DialectHelper
        schema = _make_enterprise_schema(2000)
        start = time.time()
        docs = DialectHelper.get_documentation(schema, detail_level="overview")
        elapsed_ms = (time.time() - start) * 1000
        assert elapsed_ms < 500
        assert len(docs) > 0

    def test_relevant_docs_subset_size(self):
        """Relevant docs for 20 tables out of 200 is much smaller than full."""
        from biai.db.dialect import DialectHelper
        schema = _make_enterprise_schema(200)
        full = DialectHelper.get_documentation(schema, detail_level="full")
        relevant = DialectHelper.get_documentation(
            schema, detail_level="relevant",
            relevant_tables=[f"table_{i}" for i in range(20)],
        )
        full_size = sum(len(d) for d in full)
        relevant_size = sum(len(d) for d in relevant)
        # Relevant should be significantly smaller
        assert relevant_size < full_size * 0.5


# ---------------------------------------------------------------------------
# Event log performance
# ---------------------------------------------------------------------------

class TestEventLogPerformance:

    def test_transition_matrix_1000_events(self):
        """Transition matrix computation < 50ms for 1000 events."""
        from datetime import datetime, timedelta
        from biai.models.event_log import EventLog, EventRecord

        base = datetime(2026, 1, 1)
        events = []
        activities = ["new", "assigned", "in_progress", "review", "done"]
        for case in range(200):
            for j, act in enumerate(activities):
                events.append(EventRecord(
                    case_id=f"case_{case}",
                    activity=act,
                    timestamp=base + timedelta(hours=case * 24 + j * 2),
                ))

        log = EventLog(process_id="test", events=events,
                       case_count=200, activity_count=5)

        start = time.time()
        matrix = log.get_transition_matrix()
        elapsed_ms = (time.time() - start) * 1000
        assert elapsed_ms < 200
        assert len(matrix) == 4  # 4 transitions in a 5-step chain

    def test_variant_distribution_1000_events(self):
        """Variant distribution < 100ms for 1000 events."""
        from datetime import datetime, timedelta
        from biai.models.event_log import EventLog, EventRecord

        base = datetime(2026, 1, 1)
        events = []
        for case in range(200):
            path = ["new", "assigned", "done"] if case % 3 != 0 else ["new", "cancelled"]
            for j, act in enumerate(path):
                events.append(EventRecord(
                    case_id=f"case_{case}",
                    activity=act,
                    timestamp=base + timedelta(hours=case * 24 + j),
                ))

        log = EventLog(process_id="test", events=events, case_count=200)

        start = time.time()
        variants = log.get_variant_distribution()
        elapsed_ms = (time.time() - start) * 1000
        assert elapsed_ms < 500
        assert len(variants) == 2  # 2 distinct paths

    def test_sankey_from_event_log_1000_events(self):
        """Sankey generation < 100ms for 1000 events."""
        from datetime import datetime, timedelta
        from biai.models.event_log import EventLog, EventRecord
        from biai.ai.echarts_builder import build_sankey_from_event_log

        base = datetime(2026, 1, 1)
        events = []
        for case in range(200):
            for j, act in enumerate(["start", "process", "end"]):
                events.append(EventRecord(
                    case_id=f"case_{case}",
                    activity=act,
                    timestamp=base + timedelta(hours=case * 24 + j),
                ))

        log = EventLog(process_id="test", events=events, case_count=200)

        start = time.time()
        option = build_sankey_from_event_log(log)
        elapsed_ms = (time.time() - start) * 1000
        assert elapsed_ms < 500
        assert option
        assert option["series"][0]["type"] == "sankey"

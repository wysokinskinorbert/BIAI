"""Enterprise-scale integration tests.

Tests for scenarios with multiple schemas, cross-schema FK,
large table counts, and correct domain clustering.
"""

import pytest

from biai.ai.metadata_graph import SchemaGraph
from biai.models.schema import SchemaSnapshot, TableInfo, ColumnInfo


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_cross_schema_snapshot() -> SchemaSnapshot:
    """Create schema with cross-schema FK relationships.

    Simulates: SALES schema references HR schema's EMPLOYEES table.
    """
    tables = [
        # HR schema tables
        TableInfo(name="HR.EMPLOYEES", columns=[
            ColumnInfo(name="employee_id", data_type="NUMBER", is_primary_key=True),
            ColumnInfo(name="name", data_type="VARCHAR2(100)"),
            ColumnInfo(name="department_id", data_type="NUMBER",
                       is_foreign_key=True, foreign_key_ref="HR.DEPARTMENTS.department_id"),
        ]),
        TableInfo(name="HR.DEPARTMENTS", columns=[
            ColumnInfo(name="department_id", data_type="NUMBER", is_primary_key=True),
            ColumnInfo(name="name", data_type="VARCHAR2(100)"),
        ]),
        # SALES schema tables
        TableInfo(name="SALES.ORDERS", columns=[
            ColumnInfo(name="order_id", data_type="NUMBER", is_primary_key=True),
            ColumnInfo(name="customer_id", data_type="NUMBER",
                       is_foreign_key=True, foreign_key_ref="SALES.CUSTOMERS.customer_id"),
            ColumnInfo(name="sales_rep_id", data_type="NUMBER",
                       is_foreign_key=True, foreign_key_ref="HR.EMPLOYEES.employee_id"),
            ColumnInfo(name="status", data_type="VARCHAR2(20)"),
            ColumnInfo(name="created_at", data_type="TIMESTAMP"),
        ]),
        TableInfo(name="SALES.ORDER_ITEMS", columns=[
            ColumnInfo(name="item_id", data_type="NUMBER", is_primary_key=True),
            ColumnInfo(name="order_id", data_type="NUMBER",
                       is_foreign_key=True, foreign_key_ref="SALES.ORDERS.order_id"),
            ColumnInfo(name="product_id", data_type="NUMBER",
                       is_foreign_key=True, foreign_key_ref="INVENTORY.PRODUCTS.product_id"),
            ColumnInfo(name="quantity", data_type="NUMBER"),
        ]),
        TableInfo(name="SALES.CUSTOMERS", columns=[
            ColumnInfo(name="customer_id", data_type="NUMBER", is_primary_key=True),
            ColumnInfo(name="name", data_type="VARCHAR2(100)"),
        ]),
        # INVENTORY schema tables
        TableInfo(name="INVENTORY.PRODUCTS", columns=[
            ColumnInfo(name="product_id", data_type="NUMBER", is_primary_key=True),
            ColumnInfo(name="name", data_type="VARCHAR2(100)"),
            ColumnInfo(name="warehouse_id", data_type="NUMBER",
                       is_foreign_key=True, foreign_key_ref="INVENTORY.WAREHOUSES.warehouse_id"),
        ]),
        TableInfo(name="INVENTORY.WAREHOUSES", columns=[
            ColumnInfo(name="warehouse_id", data_type="NUMBER", is_primary_key=True),
            ColumnInfo(name="location", data_type="VARCHAR2(200)"),
        ]),
    ]
    return SchemaSnapshot(tables=tables, schema_name="UNIFIED")


def _make_star_schema_snapshot() -> SchemaSnapshot:
    """Create star schema: fact table SALES_FACT with 5+ dimension FKs."""
    tables = [
        TableInfo(name="SALES_FACT", columns=[
            ColumnInfo(name="fact_id", data_type="NUMBER", is_primary_key=True),
            ColumnInfo(name="date_id", data_type="NUMBER",
                       is_foreign_key=True, foreign_key_ref="DIM_DATE.date_id"),
            ColumnInfo(name="product_id", data_type="NUMBER",
                       is_foreign_key=True, foreign_key_ref="DIM_PRODUCT.product_id"),
            ColumnInfo(name="customer_id", data_type="NUMBER",
                       is_foreign_key=True, foreign_key_ref="DIM_CUSTOMER.customer_id"),
            ColumnInfo(name="store_id", data_type="NUMBER",
                       is_foreign_key=True, foreign_key_ref="DIM_STORE.store_id"),
            ColumnInfo(name="amount", data_type="NUMBER"),
            ColumnInfo(name="quantity", data_type="NUMBER"),
        ]),
        TableInfo(name="DIM_DATE", columns=[
            ColumnInfo(name="date_id", data_type="NUMBER", is_primary_key=True),
            ColumnInfo(name="full_date", data_type="DATE"),
        ]),
        TableInfo(name="DIM_PRODUCT", columns=[
            ColumnInfo(name="product_id", data_type="NUMBER", is_primary_key=True),
            ColumnInfo(name="name", data_type="VARCHAR2(100)"),
        ]),
        TableInfo(name="DIM_CUSTOMER", columns=[
            ColumnInfo(name="customer_id", data_type="NUMBER", is_primary_key=True),
            ColumnInfo(name="name", data_type="VARCHAR2(100)"),
        ]),
        TableInfo(name="DIM_STORE", columns=[
            ColumnInfo(name="store_id", data_type="NUMBER", is_primary_key=True),
            ColumnInfo(name="location", data_type="VARCHAR2(200)"),
        ]),
    ]
    return SchemaSnapshot(tables=tables, schema_name="DW")


# ---------------------------------------------------------------------------
# Cross-schema FK tests
# ---------------------------------------------------------------------------

class TestCrossSchemaFK:

    def test_cross_schema_edges_detected(self):
        """Cross-schema FK edges are correctly identified."""
        schema = _make_cross_schema_snapshot()
        graph = SchemaGraph(schema)
        cross = graph.get_cross_schema_edges()
        # SALES.ORDERS -> HR.EMPLOYEES (cross-schema)
        # SALES.ORDER_ITEMS -> INVENTORY.PRODUCTS (cross-schema)
        assert len(cross) >= 2
        sources = {e.source_table for e in cross}
        targets = {e.target_table for e in cross}
        assert "SALES.ORDERS" in sources or "SALES.ORDER_ITEMS" in sources
        assert "HR.EMPLOYEES" in targets or "INVENTORY.PRODUCTS" in targets

    def test_cross_schema_edge_count_in_stats(self):
        """Stats correctly report cross-schema edge count."""
        schema = _make_cross_schema_snapshot()
        graph = SchemaGraph(schema)
        stats = graph.get_stats()
        assert stats.cross_schema_edges >= 2

    def test_intra_schema_not_cross(self):
        """Intra-schema FK (SALES.ORDERS -> SALES.CUSTOMERS) is NOT cross-schema."""
        schema = _make_cross_schema_snapshot()
        graph = SchemaGraph(schema)
        cross = graph.get_cross_schema_edges()
        for edge in cross:
            # Ensure no intra-schema edges in cross-schema results
            src_schema = edge.source_table.split(".")[0] if "." in edge.source_table else ""
            tgt_schema = edge.target_table.split(".")[0] if "." in edge.target_table else ""
            if src_schema and tgt_schema:
                assert src_schema != tgt_schema


# ---------------------------------------------------------------------------
# Star schema detection
# ---------------------------------------------------------------------------

class TestStarSchemaDetection:

    def test_star_schema_detected(self):
        """Star schema with fact table + 4 dimensions is detected."""
        schema = _make_star_schema_snapshot()
        graph = SchemaGraph(schema)
        stars = graph.find_star_schemas()
        assert len(stars) >= 1
        fact = stars[0]
        assert fact.fact_table == "SALES_FACT"
        assert len(fact.dimension_tables) >= 3

    def test_star_schema_in_stats(self):
        """Stats include star schema detection."""
        schema = _make_star_schema_snapshot()
        graph = SchemaGraph(schema)
        stats = graph.get_stats()
        assert len(stats.star_schemas) >= 1


# ---------------------------------------------------------------------------
# Connected components / domain clustering
# ---------------------------------------------------------------------------

class TestDomainClustering:

    def test_connected_components(self):
        """Cross-schema snapshot is fully connected (1 component)."""
        schema = _make_cross_schema_snapshot()
        graph = SchemaGraph(schema)
        components = graph.find_connected_components()
        # All tables are connected via FK → 1 component
        assert len(components) == 1

    def test_disconnected_components(self):
        """Two isolated table groups form 2 components."""
        tables = [
            TableInfo(name="A", columns=[
                ColumnInfo(name="id", data_type="INT", is_primary_key=True),
            ]),
            TableInfo(name="B", columns=[
                ColumnInfo(name="id", data_type="INT", is_primary_key=True),
                ColumnInfo(name="a_id", data_type="INT",
                           is_foreign_key=True, foreign_key_ref="A.id"),
            ]),
            # Isolated group
            TableInfo(name="X", columns=[
                ColumnInfo(name="id", data_type="INT", is_primary_key=True),
            ]),
            TableInfo(name="Y", columns=[
                ColumnInfo(name="id", data_type="INT", is_primary_key=True),
                ColumnInfo(name="x_id", data_type="INT",
                           is_foreign_key=True, foreign_key_ref="X.id"),
            ]),
        ]
        schema = SchemaSnapshot(tables=tables, schema_name="test")
        graph = SchemaGraph(schema)
        components = graph.find_connected_components()
        assert len(components) == 2

    def test_community_detection_returns_all_tables(self):
        """Community detection assigns every table to a community."""
        schema = _make_cross_schema_snapshot()
        graph = SchemaGraph(schema)
        communities = graph.find_table_communities()
        table_names = {t.name for t in schema.tables}
        assert set(communities.keys()) == table_names


# ---------------------------------------------------------------------------
# Hub detection
# ---------------------------------------------------------------------------

class TestHubDetection:

    def test_hub_tables_in_cross_schema(self):
        """Tables with most FK references are detected as hubs."""
        schema = _make_cross_schema_snapshot()
        graph = SchemaGraph(schema)
        stats = graph.get_stats()
        hub_names = {name for name, _ in stats.hub_tables}
        # HR.EMPLOYEES is referenced by SALES.ORDERS (cross-schema)
        # SALES.ORDERS is referenced by SALES.ORDER_ITEMS
        # These should appear as hubs
        assert len(stats.hub_tables) > 0


# ---------------------------------------------------------------------------
# Bridge table detection
# ---------------------------------------------------------------------------

class TestBridgeTableDetection:

    def test_bridge_tables(self):
        """Tables with only FK columns (no own data) are bridge tables."""
        tables = [
            TableInfo(name="USERS", columns=[
                ColumnInfo(name="id", data_type="INT", is_primary_key=True),
                ColumnInfo(name="name", data_type="VARCHAR(100)"),
            ]),
            TableInfo(name="ROLES", columns=[
                ColumnInfo(name="id", data_type="INT", is_primary_key=True),
                ColumnInfo(name="name", data_type="VARCHAR(100)"),
            ]),
            # Bridge: only PKs + FKs, no own data columns
            TableInfo(name="USER_ROLES", columns=[
                ColumnInfo(name="user_id", data_type="INT",
                           is_foreign_key=True, foreign_key_ref="USERS.id"),
                ColumnInfo(name="role_id", data_type="INT",
                           is_foreign_key=True, foreign_key_ref="ROLES.id"),
            ]),
        ]
        schema = SchemaSnapshot(tables=tables, schema_name="test")
        graph = SchemaGraph(schema)
        bridges = graph.find_bridge_tables()
        assert "USER_ROLES" in bridges

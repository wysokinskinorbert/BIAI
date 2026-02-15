"""Tests for SchemaGraph metadata analysis."""

import pytest

from biai.ai.metadata_graph import SchemaGraph, FKEdge, StarSchema
from biai.models.schema import SchemaSnapshot, TableInfo, ColumnInfo


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_snapshot():
    """Simple schema: orders -> customers, order_items -> orders, order_items -> products."""
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
        ],
        db_type="postgresql",
        schema_name="public",
    )


@pytest.fixture
def star_schema_snapshot():
    """Star schema: SALES fact table with 4 dimension FKs."""
    return SchemaSnapshot(
        tables=[
            TableInfo(
                name="SALES", schema_name="dw",
                columns=[
                    ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
                    ColumnInfo(name="CUSTOMER_ID", data_type="INTEGER",
                               is_foreign_key=True, foreign_key_ref="DIM_CUSTOMER"),
                    ColumnInfo(name="PRODUCT_ID", data_type="INTEGER",
                               is_foreign_key=True, foreign_key_ref="DIM_PRODUCT"),
                    ColumnInfo(name="DATE_ID", data_type="INTEGER",
                               is_foreign_key=True, foreign_key_ref="DIM_DATE"),
                    ColumnInfo(name="STORE_ID", data_type="INTEGER",
                               is_foreign_key=True, foreign_key_ref="DIM_STORE"),
                    ColumnInfo(name="AMOUNT", data_type="DECIMAL"),
                ],
            ),
            TableInfo(name="DIM_CUSTOMER", schema_name="dw", columns=[
                ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
            ]),
            TableInfo(name="DIM_PRODUCT", schema_name="dw", columns=[
                ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
            ]),
            TableInfo(name="DIM_DATE", schema_name="dw", columns=[
                ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
            ]),
            TableInfo(name="DIM_STORE", schema_name="dw", columns=[
                ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
            ]),
        ],
        db_type="postgresql",
    )


@pytest.fixture
def cross_schema_snapshot():
    """Cross-schema FK: sales.orders references hr.employees."""
    return SchemaSnapshot(
        tables=[
            TableInfo(
                name="ORDERS", schema_name="SALES",
                columns=[
                    ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
                    ColumnInfo(name="EMPLOYEE_ID", data_type="INTEGER",
                               is_foreign_key=True, foreign_key_ref="HR.EMPLOYEES"),
                ],
            ),
            TableInfo(
                name="EMPLOYEES", schema_name="HR",
                columns=[
                    ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
                    ColumnInfo(name="NAME", data_type="VARCHAR(100)"),
                ],
            ),
        ],
        db_type="oracle",
    )


@pytest.fixture
def bridge_table_snapshot():
    """Bridge table: STUDENT_COURSES has only FK+PK columns."""
    return SchemaSnapshot(
        tables=[
            TableInfo(name="STUDENTS", columns=[
                ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
            ]),
            TableInfo(name="COURSES", columns=[
                ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True),
            ]),
            TableInfo(name="STUDENT_COURSES", columns=[
                ColumnInfo(name="STUDENT_ID", data_type="INTEGER",
                           is_primary_key=True, is_foreign_key=True,
                           foreign_key_ref="STUDENTS"),
                ColumnInfo(name="COURSE_ID", data_type="INTEGER",
                           is_primary_key=True, is_foreign_key=True,
                           foreign_key_ref="COURSES"),
            ]),
        ],
        db_type="postgresql",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSchemaGraph:

    def test_build_from_snapshot(self, simple_snapshot):
        graph = SchemaGraph(simple_snapshot)
        assert graph.table_count == 4
        assert graph.edge_count == 3  # 3 FK relationships

    def test_out_degree(self, simple_snapshot):
        graph = SchemaGraph(simple_snapshot)
        assert graph.get_out_degree("ORDER_ITEMS") == 2  # -> ORDERS, -> PRODUCTS
        assert graph.get_out_degree("ORDERS") == 1  # -> CUSTOMERS
        assert graph.get_out_degree("CUSTOMERS") == 0

    def test_in_degree(self, simple_snapshot):
        graph = SchemaGraph(simple_snapshot)
        assert graph.get_in_degree("CUSTOMERS") == 1  # from ORDERS
        assert graph.get_in_degree("ORDERS") == 1  # from ORDER_ITEMS
        assert graph.get_in_degree("PRODUCTS") == 1  # from ORDER_ITEMS
        assert graph.get_in_degree("ORDER_ITEMS") == 0

    def test_find_hubs(self, simple_snapshot):
        graph = SchemaGraph(simple_snapshot)
        hubs = graph.find_hubs(top_n=5)
        # ORDER_ITEMS and ORDERS both have degree 2 (tied for top)
        top_names = {h[0] for h in hubs[:2]}
        assert "ORDER_ITEMS" in top_names
        assert "ORDERS" in top_names
        assert hubs[0][1] == 2

    def test_connected_components(self, simple_snapshot):
        graph = SchemaGraph(simple_snapshot)
        components = graph.find_connected_components()
        # All tables connected → 1 component
        assert len(components) == 1
        assert len(components[0]) == 4

    def test_star_schema_detection(self, star_schema_snapshot):
        graph = SchemaGraph(star_schema_snapshot)
        stars = graph.find_star_schemas(min_dimensions=3)
        assert len(stars) >= 1
        # SALES is the fact table with 4 dimension FKs
        fact = stars[0]
        assert fact.fact_table == "SALES"
        assert fact.fk_count == 4

    def test_bridge_table_detection(self, bridge_table_snapshot):
        graph = SchemaGraph(bridge_table_snapshot)
        bridges = graph.find_bridge_tables()
        assert "STUDENT_COURSES" in bridges

    def test_cross_schema_edges(self, cross_schema_snapshot):
        graph = SchemaGraph(cross_schema_snapshot)
        cross = graph.get_cross_schema_edges()
        assert len(cross) == 1
        assert cross[0].source_schema == "SALES"
        assert cross[0].target_schema == "HR"

    def test_fk_chains(self, simple_snapshot):
        graph = SchemaGraph(simple_snapshot)
        chains = graph.find_fk_chains(min_length=2)
        # ORDER_ITEMS -> ORDERS -> CUSTOMERS is a chain of length 3
        found_long_chain = any(len(c) >= 3 for c in chains)
        assert found_long_chain

    def test_community_detection(self, simple_snapshot):
        graph = SchemaGraph(simple_snapshot)
        communities = graph.find_table_communities()
        assert len(communities) == 4  # all 4 tables assigned

    def test_get_stats(self, simple_snapshot):
        graph = SchemaGraph(simple_snapshot)
        stats = graph.get_stats()
        assert stats.total_tables == 4
        assert stats.total_edges == 3
        assert stats.connected_components == 1

    def test_empty_snapshot(self):
        graph = SchemaGraph(SchemaSnapshot())
        assert graph.table_count == 0
        assert graph.edge_count == 0
        stats = graph.get_stats()
        assert stats.total_tables == 0

    def test_case_insensitive_lookup(self, simple_snapshot):
        graph = SchemaGraph(simple_snapshot)
        assert graph.get_out_degree("orders") == 1
        assert graph.get_in_degree("customers") == 1

    def test_performance_200_tables(self):
        """Graph operations should complete quickly for 200 tables."""
        import time

        tables = []
        for i in range(200):
            cols = [ColumnInfo(name="ID", data_type="INTEGER", is_primary_key=True)]
            if i > 0:
                # Each table references the previous one
                cols.append(ColumnInfo(
                    name="PARENT_ID", data_type="INTEGER",
                    is_foreign_key=True,
                    foreign_key_ref=f"TABLE_{i - 1}",
                ))
            tables.append(TableInfo(name=f"TABLE_{i}", columns=cols))

        snapshot = SchemaSnapshot(tables=tables, db_type="test")

        start = time.time()
        graph = SchemaGraph(snapshot)
        build_time = time.time() - start

        start = time.time()
        graph.find_hubs()
        graph.find_connected_components()
        graph.find_bridge_tables()
        graph.find_star_schemas()
        graph.find_table_communities()
        analysis_time = time.time() - start

        assert build_time < 1.0, f"Build took {build_time:.2f}s (should be <1s)"
        assert analysis_time < 5.0, f"Analysis took {analysis_time:.2f}s (should be <5s)"
        assert graph.table_count == 200
        assert graph.edge_count == 199

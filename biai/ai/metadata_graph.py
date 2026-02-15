"""Metadata graph for enterprise-scale schema analysis.

Provides graph-based analysis of database schemas using a hybrid approach:
- Fast dict-based adjacency for common operations (neighbor lookup, degree)
- Lazy networkx DiGraph for advanced algorithms (community detection, centrality)

Designed to handle 2000+ tables efficiently.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

import networkx as nx

from biai.models.schema import SchemaSnapshot, TableInfo
from biai.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FKEdge:
    """Foreign key relationship edge."""
    source_table: str
    source_column: str
    target_table: str
    source_schema: str = ""
    target_schema: str = ""

    @property
    def is_cross_schema(self) -> bool:
        return bool(
            self.source_schema and self.target_schema
            and self.source_schema != self.target_schema
        )


@dataclass
class StarSchema:
    """Detected star schema pattern (fact + dimensions)."""
    fact_table: str
    dimension_tables: list[str] = field(default_factory=list)
    fk_count: int = 0


@dataclass
class GraphStats:
    """Summary statistics from graph analysis."""
    total_tables: int = 0
    total_edges: int = 0
    connected_components: int = 0
    hub_tables: list[tuple[str, int]] = field(default_factory=list)
    star_schemas: list[StarSchema] = field(default_factory=list)
    bridge_tables: list[str] = field(default_factory=list)
    cross_schema_edges: int = 0


class SchemaGraph:
    """Unified metadata graph across multiple schemas.

    Hybrid approach: dict adjacency for fast traversal + lazy networkx
    for graph algorithms (community detection, centrality, etc.).
    """

    def __init__(self, snapshot: SchemaSnapshot):
        # Fast dict-based adjacency
        self._outgoing: dict[str, list[FKEdge]] = defaultdict(list)
        self._incoming: dict[str, list[FKEdge]] = defaultdict(list)
        self._tables: dict[str, TableInfo] = {}
        self._table_names: set[str] = set()

        # Lazy networkx graph (built on first algorithm call)
        self._nx: nx.DiGraph | None = None

        self._build_from_snapshot(snapshot)

    def _build_from_snapshot(self, snapshot: SchemaSnapshot) -> None:
        """Build adjacency structures from schema snapshot."""
        for table in snapshot.tables:
            key = table.name.upper()
            self._tables[key] = table
            self._table_names.add(key)

        for table in snapshot.tables:
            src_key = table.name.upper()
            src_schema = self._extract_schema(table)
            for col in table.columns:
                if col.is_foreign_key and col.foreign_key_ref:
                    tgt_table, tgt_schema = self._resolve_fk_target(
                        col.foreign_key_ref, src_schema,
                    )

                    edge = FKEdge(
                        source_table=src_key,
                        source_column=col.name,
                        target_table=tgt_table,
                        source_schema=src_schema,
                        target_schema=tgt_schema,
                    )
                    self._outgoing[src_key].append(edge)
                    self._incoming[tgt_table].append(edge)

        logger.info(
            "schema_graph_built",
            tables=len(self._table_names),
            edges=sum(len(v) for v in self._outgoing.values()),
        )

    @staticmethod
    def _extract_schema(table: TableInfo) -> str:
        """Extract schema name from table info or table name."""
        if table.schema_name:
            return table.schema_name.upper()
        if "." in table.name:
            return table.name.split(".")[0].upper()
        return ""

    def _resolve_fk_target(
        self, ref: str, fallback_schema: str = "",
    ) -> tuple[str, str]:
        """Resolve FK reference to (target_table_key, target_schema).

        Handles these formats:
        - ``TABLE.column`` → (``TABLE``, ``""``)
        - ``SCHEMA.TABLE`` → (``TABLE``, ``SCHEMA``) — column omitted
        - ``SCHEMA.TABLE.column`` → (``SCHEMA.TABLE``, ``SCHEMA``)

        Uses longest-match against known table names for unambiguous
        resolution when table names themselves contain dots.
        """
        ref_upper = ref.upper()

        # Try matching against known table names (longest match wins).
        # This handles schema-prefixed table names like "HR.EMPLOYEES"
        # where ref is "HR.EMPLOYEES.employee_id".
        best_match = ""
        for table_name in self._table_names:
            prefix = table_name + "."
            if ref_upper.startswith(prefix) and len(table_name) > len(best_match):
                best_match = table_name

        # Also check for exact match (ref IS the table name, no column)
        if not best_match and ref_upper in self._table_names:
            best_match = ref_upper

        if best_match:
            schema = best_match.split(".")[0] if "." in best_match else ""
            return best_match, schema

        # Fallback: split on dots
        parts = ref.split(".")
        if len(parts) >= 3:
            # Assume SCHEMA.TABLE.COLUMN
            qualified = f"{parts[0]}.{parts[1]}".upper()
            return qualified, parts[0].upper()
        elif len(parts) == 2:
            p0, p1 = parts[0].upper(), parts[1].upper()
            # If second part is a known table and first is not → SCHEMA.TABLE
            if p1 in self._table_names and p0 not in self._table_names:
                return p1, p0
            # Otherwise TABLE.COLUMN
            if p0 in self._table_names:
                return p0, fallback_schema
            # Neither matched → try qualified name
            qualified = f"{p0}.{p1}"
            if qualified in self._table_names:
                return qualified, p0
            return p0, fallback_schema
        return ref.upper(), fallback_schema

    def _ensure_nx(self) -> nx.DiGraph:
        """Lazily build networkx graph."""
        if self._nx is not None:
            return self._nx

        G = nx.DiGraph()
        for table_name in self._table_names:
            G.add_node(table_name)
        for edges in self._outgoing.values():
            for edge in edges:
                G.add_edge(
                    edge.source_table, edge.target_table,
                    column=edge.source_column,
                    cross_schema=edge.is_cross_schema,
                )
        self._nx = G
        return G

    # ----------------------------------------------------------------
    # Fast dict-based operations
    # ----------------------------------------------------------------

    @property
    def table_count(self) -> int:
        return len(self._table_names)

    @property
    def edge_count(self) -> int:
        return sum(len(v) for v in self._outgoing.values())

    def get_fk_neighbors(self, table: str) -> list[FKEdge]:
        """Get outgoing FK edges from a table."""
        return self._outgoing.get(table.upper(), [])

    def get_incoming_fks(self, table: str) -> list[FKEdge]:
        """Get incoming FK edges to a table (tables referencing this one)."""
        return self._incoming.get(table.upper(), [])

    def get_out_degree(self, table: str) -> int:
        """Number of FK references FROM this table."""
        return len(self._outgoing.get(table.upper(), []))

    def get_in_degree(self, table: str) -> int:
        """Number of FK references TO this table."""
        return len(self._incoming.get(table.upper(), []))

    def get_total_degree(self, table: str) -> int:
        return self.get_out_degree(table) + self.get_in_degree(table)

    def get_table_info(self, table: str) -> TableInfo | None:
        return self._tables.get(table.upper())

    # ----------------------------------------------------------------
    # NetworkX-powered analysis
    # ----------------------------------------------------------------

    def find_hubs(self, top_n: int = 20) -> list[tuple[str, int]]:
        """Tables with most FK references (by total degree)."""
        degrees = [
            (name, self.get_total_degree(name))
            for name in self._table_names
        ]
        degrees.sort(key=lambda x: x[1], reverse=True)
        return degrees[:top_n]

    def find_connected_components(self) -> list[set[str]]:
        """Isolated table clusters (potential business domains)."""
        G = self._ensure_nx()
        # Use undirected view for connected components
        components = list(nx.connected_components(G.to_undirected()))
        # Sort by size (largest first)
        components.sort(key=len, reverse=True)
        return components

    def find_star_schemas(self, min_dimensions: int = 3) -> list[StarSchema]:
        """Fact tables with N+ dimension FKs (analytical patterns)."""
        results = []
        for table_name in self._table_names:
            out_edges = self._outgoing.get(table_name, [])
            if len(out_edges) >= min_dimensions:
                # Table references many others → potential fact table
                dims = list({e.target_table for e in out_edges})
                results.append(StarSchema(
                    fact_table=table_name,
                    dimension_tables=dims,
                    fk_count=len(out_edges),
                ))
        results.sort(key=lambda s: s.fk_count, reverse=True)
        return results

    def find_bridge_tables(self) -> list[str]:
        """Tables with only FK columns (many-to-many connectors)."""
        bridges = []
        for table_name, table_info in self._tables.items():
            if not table_info.columns:
                continue
            fk_cols = sum(1 for c in table_info.columns if c.is_foreign_key)
            pk_cols = sum(1 for c in table_info.columns if c.is_primary_key)
            total = len(table_info.columns)
            # Bridge: most columns are FKs (or FK+PK)
            if fk_cols >= 2 and (fk_cols + pk_cols) >= total * 0.8:
                bridges.append(table_name)
        return bridges

    def find_fk_chains(self, min_length: int = 3) -> list[list[str]]:
        """FK chains of length N+ (potential process flows)."""
        G = self._ensure_nx()
        chains = []

        # Find all simple paths of min_length from nodes with in_degree=0
        # or just explore from each node
        for node in G.nodes():
            if G.in_degree(node) == 0 or G.in_degree(node) < G.out_degree(node):
                # Potential chain start
                for target in G.nodes():
                    if target == node:
                        continue
                    try:
                        for path in nx.all_simple_paths(G, node, target, cutoff=8):
                            if len(path) >= min_length:
                                chains.append(path)
                    except (nx.NetworkXError, nx.NodeNotFound):
                        continue

        # Deduplicate and sort by length
        seen = set()
        unique_chains = []
        for chain in chains:
            key = tuple(chain)
            if key not in seen:
                seen.add(key)
                unique_chains.append(chain)
        unique_chains.sort(key=len, reverse=True)
        return unique_chains[:50]  # Limit to top 50

    def find_table_communities(self) -> dict[str, int]:
        """Community detection using Louvain algorithm.

        Returns mapping of table_name → community_id.
        """
        G = self._ensure_nx()
        if G.number_of_nodes() == 0:
            return {}

        undirected = G.to_undirected()
        try:
            communities = nx.community.louvain_communities(
                undirected, seed=42, resolution=1.0,
            )
            result = {}
            for idx, community in enumerate(communities):
                for node in community:
                    result[node] = idx
            return result
        except Exception as e:
            logger.warning("community_detection_failed", error=str(e))
            return {}

    def get_cross_schema_edges(self) -> list[FKEdge]:
        """FK refs crossing schema boundaries."""
        cross = []
        for edges in self._outgoing.values():
            for edge in edges:
                if edge.is_cross_schema:
                    cross.append(edge)
        return cross

    # ----------------------------------------------------------------
    # Aggregate statistics
    # ----------------------------------------------------------------

    def get_stats(self) -> GraphStats:
        """Compute aggregate graph statistics."""
        components = self.find_connected_components()
        return GraphStats(
            total_tables=self.table_count,
            total_edges=self.edge_count,
            connected_components=len(components),
            hub_tables=self.find_hubs(top_n=10),
            star_schemas=self.find_star_schemas(),
            bridge_tables=self.find_bridge_tables(),
            cross_schema_edges=len(self.get_cross_schema_edges()),
        )

"""Business context DTO — aggregated context for AI pipeline."""

from pydantic import BaseModel, Field

from biai.models.discovery import DiscoveredProcess
from biai.models.schema import SchemaSnapshot


class BusinessContext(BaseModel):
    """Unified business context from schema analysis, discovery, and profiling.

    Used by:
    - AIPipeline for Vanna training enrichment
    - SchemaState for progressive UI updates
    - ProcessGraphBuilder for evidence-based flow diagrams
    """

    # Schema structure
    schema: SchemaSnapshot | None = None

    # Graph analysis results
    hub_tables: list[tuple[str, int]] = Field(default_factory=list)
    connected_components: int = 0
    star_schemas: list[dict] = Field(default_factory=list)
    bridge_tables: list[str] = Field(default_factory=list)
    cross_schema_edges: int = 0
    table_communities: dict[str, int] = Field(default_factory=dict)

    # Discovered processes
    processes: list[DiscoveredProcess] = Field(default_factory=list)

    # Table profiles (table_name -> profile dict)
    profiles: dict[str, dict] = Field(default_factory=dict)

    # Business glossary (table_name -> glossary dict)
    glossary: dict[str, dict] = Field(default_factory=dict)

    # Metadata
    discovered_at: str = ""
    discovery_duration_ms: int = 0

    @property
    def domain_map(self) -> dict[int, list[str]]:
        """Community ID → list of tables."""
        result: dict[int, list[str]] = {}
        for table, community_id in self.table_communities.items():
            result.setdefault(community_id, []).append(table)
        return result

    @property
    def process_summary(self) -> list[dict]:
        """Summary for UI cards."""
        return [
            {
                "id": p.id,
                "name": p.name,
                "tables": p.tables,
                "stages": len(p.stages),
                "confidence": round(p.confidence, 2),
                "evidence_count": len(p.evidence),
            }
            for p in self.processes
        ]

    @property
    def has_graph_analysis(self) -> bool:
        return len(self.hub_tables) > 0 or self.connected_components > 0

    @property
    def has_processes(self) -> bool:
        return len(self.processes) > 0

    @property
    def has_profiles(self) -> bool:
        return len(self.profiles) > 0

    @property
    def has_glossary(self) -> bool:
        return len(self.glossary) > 0

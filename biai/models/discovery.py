"""Models for dynamic process discovery."""

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """A single piece of evidence supporting a process discovery."""

    signal_type: str  # "status_column", "transition_table", "fk_chain",
    # "timestamp_sequence", "trigger_on_status", "hub_table",
    # "star_schema_fact", "bridge_table"
    description: str
    strength: float = 0.0  # 0.0 - 1.0
    source_table: str = ""
    source_column: str = ""


class ColumnCandidate(BaseModel):
    """A column that may represent a process status or timestamp."""

    table_name: str
    column_name: str
    role: str  # "status" | "timestamp" | "duration"
    distinct_values: list[str] = Field(default_factory=list)
    cardinality: int = 0
    confidence: float = 0.0


class TransitionPattern(BaseModel):
    """A detected from/to transition pattern in a table."""

    table_name: str
    from_column: str
    to_column: str
    count_column: str | None = None
    timestamp_column: str | None = None
    transitions: list[tuple[str, str, int]] = Field(default_factory=list)


class EntityChain(BaseModel):
    """A chain of tables connected by FK representing a process entity."""

    tables: list[str] = Field(default_factory=list)
    join_keys: list[tuple[str, str]] = Field(default_factory=list)
    entity_name: str = ""


class DiscoveredProcess(BaseModel):
    """A business process discovered from schema and data analysis."""

    id: str
    name: str
    description: str = ""
    tables: list[str] = Field(default_factory=list)

    # Discovery sources
    status_column: ColumnCandidate | None = None
    transition_pattern: TransitionPattern | None = None
    entity_chain: EntityChain | None = None

    # Process structure
    stages: list[str] = Field(default_factory=list)
    stage_counts: dict[str, int] = Field(default_factory=dict)
    branches: dict[str, list[str]] = Field(default_factory=dict)

    # Evidence supporting this process
    evidence: list[Evidence] = Field(default_factory=list)

    # Overall quality score (0.0 - 1.0)
    confidence: float = 0.0

    # AI-enriched metadata
    ai_labels: dict[str, str] = Field(default_factory=dict)
    ai_colors: dict[str, str] = Field(default_factory=dict)
    ai_icons: dict[str, str] = Field(default_factory=dict)

    def get_label(self, stage_id: str) -> str:
        """Get human-readable label for a stage."""
        if stage_id in self.ai_labels:
            return self.ai_labels[stage_id]
        return stage_id.replace("_", " ").title()

    def get_stage_color(self, stage_id: str) -> str | None:
        """Get AI-suggested color for a stage, or None."""
        return self.ai_colors.get(stage_id)

    def get_stage_icon(self, stage_id: str) -> str | None:
        """Get AI-suggested icon for a stage, or None."""
        return self.ai_icons.get(stage_id)

    def to_serializable(self) -> dict:
        """Convert to JSON-serializable dict for Reflex state."""
        return self.model_dump()

    @classmethod
    def from_serializable(cls, data: dict) -> "DiscoveredProcess":
        """Restore from serialized dict."""
        return cls.model_validate(data)

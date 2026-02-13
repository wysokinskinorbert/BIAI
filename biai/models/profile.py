"""Data profiling models for auto-profiling columns and tables."""

from enum import Enum

from pydantic import BaseModel, Field


class SemanticType(str, Enum):
    """Detected semantic type for a column."""
    ID = "id"
    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    STATUS = "status"
    CATEGORY = "category"
    QUANTITY = "quantity"
    URL = "url"
    CODE = "code"
    TEXT = "text"
    NUMERIC = "numeric"
    UNKNOWN = "unknown"


class ColumnStats(BaseModel):
    """Statistical summary for a single column."""
    min_value: str | None = None
    max_value: str | None = None
    mean: float | None = None
    median: float | None = None
    std: float | None = None
    null_count: int = 0
    null_pct: float = 0.0
    distinct_count: int = 0
    distinct_pct: float = 0.0
    top_values: list[dict] = Field(default_factory=list)  # [{value, count}]


class Anomaly(BaseModel):
    """Detected data anomaly."""
    type: str  # outlier, null_spike, suspicious_pattern
    description: str
    severity: str = "low"  # low, medium, high


class ColumnProfile(BaseModel):
    """Complete profile of a single column."""
    column_name: str
    data_type: str
    semantic_type: SemanticType = SemanticType.UNKNOWN
    stats: ColumnStats = Field(default_factory=ColumnStats)
    anomalies: list[Anomaly] = Field(default_factory=list)
    sample_values: list[str] = Field(default_factory=list)


class TableProfile(BaseModel):
    """Complete profile of a table."""
    table_name: str
    schema_name: str = ""
    row_count: int = 0
    column_profiles: list[ColumnProfile] = Field(default_factory=list)
    sample_rows: list[dict] = Field(default_factory=list)
    profiled_at: str | None = None

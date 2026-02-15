"""Database schema models."""

from pydantic import BaseModel, Field


class ColumnInfo(BaseModel):
    """Database column information."""
    name: str
    data_type: str
    nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_key_ref: str | None = None
    comment: str | None = None


class TableInfo(BaseModel):
    """Database table information."""
    name: str
    schema_name: str = ""
    columns: list[ColumnInfo] = Field(default_factory=list)
    row_count: int | None = None
    comment: str | None = None
    object_type: str = "TABLE"  # "TABLE", "VIEW", "MATERIALIZED_VIEW"

    @property
    def full_name(self) -> str:
        if self.schema_name:
            return f"{self.schema_name}.{self.name}"
        return self.name

    def get_ddl(self) -> str:
        """Generate DDL-like representation for training."""
        cols = []
        for col in self.columns:
            parts = [f"  {col.name} {col.data_type}"]
            if col.is_primary_key:
                parts.append("PRIMARY KEY")
            if not col.nullable:
                parts.append("NOT NULL")
            if col.foreign_key_ref:
                parts.append(f"REFERENCES {col.foreign_key_ref}")
            cols.append(" ".join(parts))
        cols_str = ",\n".join(cols)
        return f"CREATE TABLE {self.full_name} (\n{cols_str}\n);"


class TriggerInfo(BaseModel):
    """Database trigger information."""
    trigger_name: str
    table_name: str
    trigger_event: str = ""  # "INSERT", "UPDATE", "DELETE", or combos
    timing: str = ""  # "BEFORE", "AFTER", "INSTEAD OF"
    trigger_body: str = ""  # truncated source code
    schema_name: str = ""


class ProcedureInfo(BaseModel):
    """Stored procedure/function/package information."""
    name: str
    object_type: str = "PROCEDURE"  # "PROCEDURE", "FUNCTION", "PACKAGE"
    schema_name: str = ""
    sub_program: str = ""  # for package members


class DependencyInfo(BaseModel):
    """Object dependency (which proc uses which table)."""
    name: str
    object_type: str = ""  # "PROCEDURE", "FUNCTION", "TRIGGER", etc.
    referenced_name: str = ""
    referenced_type: str = ""  # "TABLE", "VIEW", etc.
    schema_name: str = ""


class SchemaSnapshot(BaseModel):
    """Complete schema snapshot."""
    tables: list[TableInfo] = Field(default_factory=list)
    triggers: list[TriggerInfo] = Field(default_factory=list)
    procedures: list[ProcedureInfo] = Field(default_factory=list)
    dependencies: list[DependencyInfo] = Field(default_factory=list)
    db_type: str = ""
    schema_name: str = ""
    cached_at: str | None = None

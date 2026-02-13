"""Business glossary models — AI-generated descriptions of tables and columns."""

from pydantic import BaseModel, Field


class ColumnDescription(BaseModel):
    """AI-generated business description of a column."""
    name: str
    description: str = ""
    business_name: str = ""  # human-friendly alias
    examples: str = ""  # example values explanation


class TableDescription(BaseModel):
    """AI-generated business description of a table."""
    name: str
    description: str = ""
    business_name: str = ""
    business_domain: str = ""  # e.g. "Sales", "HR", "Inventory"
    columns: list[ColumnDescription] = Field(default_factory=list)


class BusinessGlossary(BaseModel):
    """Complete business glossary for a database schema."""
    db_name: str = ""
    tables: list[TableDescription] = Field(default_factory=list)
    generated_at: str | None = None

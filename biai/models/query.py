"""Query result models."""

from pydantic import BaseModel, Field
import pandas as pd


class SQLQuery(BaseModel):
    """Generated SQL query."""
    sql: str
    dialect: str = ""
    is_valid: bool = False
    validation_error: str | None = None
    generation_attempt: int = 1


class QueryResult(BaseModel):
    """Query execution result."""
    model_config = {"arbitrary_types_allowed": True}

    sql: str
    columns: list[str] = Field(default_factory=list)
    rows: list[list] = Field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    truncated: bool = False
    error: str | None = None

    def to_dataframe(self) -> pd.DataFrame:
        if not self.rows:
            return pd.DataFrame()
        return pd.DataFrame(self.rows, columns=self.columns)

    def to_csv(self) -> str:
        return self.to_dataframe().to_csv(index=False)


class QueryError(BaseModel):
    """Query execution error."""
    sql: str
    error_message: str
    error_code: str | None = None
    attempt: int = 1

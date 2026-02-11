"""Data formatting utilities."""

from typing import Any
import pandas as pd


def format_number(value: Any) -> str:
    """Format a number for display."""
    if value is None:
        return "-"
    if isinstance(value, float):
        if value == int(value):
            return f"{int(value):,}"
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def format_dataframe_for_display(df: pd.DataFrame, max_rows: int = 100) -> list[dict]:
    """Convert DataFrame to list of dicts for Reflex table display."""
    truncated = df.head(max_rows)
    records = []
    for _, row in truncated.iterrows():
        records.append({col: format_number(val) for col, val in row.items()})
    return records


def truncate_sql(sql: str, max_length: int = 500) -> str:
    """Truncate SQL for display."""
    sql = sql.strip()
    if len(sql) <= max_length:
        return sql
    return sql[:max_length] + "..."

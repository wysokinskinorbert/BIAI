"""Data export utilities."""

import io
import pandas as pd

from biai.config.constants import CSV_MAX_ROWS


def export_csv(df: pd.DataFrame, max_rows: int = CSV_MAX_ROWS) -> str:
    """Export DataFrame to CSV string."""
    truncated = df.head(max_rows)
    return truncated.to_csv(index=False)


def export_csv_bytes(df: pd.DataFrame, max_rows: int = CSV_MAX_ROWS) -> bytes:
    """Export DataFrame to CSV bytes (for download)."""
    truncated = df.head(max_rows)
    buffer = io.BytesIO()
    truncated.to_csv(buffer, index=False)
    return buffer.getvalue()

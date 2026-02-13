"""Query state for SQL viewer and data table."""

import math

import reflex as rx

from biai.config.constants import DISPLAY_ROW_LIMIT


def _cell_to_str(cell) -> str:
    """Convert a cell value to display string, replacing None/nan with empty string."""
    if cell is None:
        return ""
    if isinstance(cell, float) and math.isnan(cell):
        return ""
    s = str(cell)
    if s in ("None", "nan", "NaN", "NaT"):
        return ""
    return s


class QueryState(rx.State):
    """Manages current query state, SQL display, and data table."""

    # SQL
    current_sql: str = ""
    sql_dialect: str = ""
    generation_attempts: int = 0
    sql_expanded: bool = False

    # Data table - use list[list[str]] for Reflex foreach compatibility
    columns: list[str] = []
    rows: list[list[str]] = []
    row_count: int = 0
    execution_time_ms: float = 0.0
    is_truncated: bool = False
    table_page: int = 0
    _PAGE_SIZE: int = 15

    # Sorting
    sort_column: str = ""
    sort_ascending: bool = True

    def set_query_result(
        self,
        sql: str,
        columns: list[str],
        rows: list[list],
        row_count: int,
        execution_time_ms: float,
        truncated: bool = False,
        dialect: str = "",
        attempts: int = 1,
    ):
        self.current_sql = sql
        self.columns = columns
        # Convert all values to strings for Reflex foreach compatibility
        # Replace None/nan with empty string for clean display
        self.rows = [[_cell_to_str(cell) for cell in row] for row in rows]
        self.row_count = row_count
        self.execution_time_ms = execution_time_ms
        self.is_truncated = truncated
        self.sql_dialect = dialect
        self.generation_attempts = attempts

    def clear_result(self):
        self.current_sql = ""
        self.columns = []
        self.rows = []
        self.row_count = 0
        self.execution_time_ms = 0.0
        self.is_truncated = False
        self.sql_expanded = False
        self.table_page = 0
        self.sort_column = ""
        self.sort_ascending = True

    def sort_by(self, column: str):
        """Sort table by column. Toggle direction if same column clicked."""
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True
        self.table_page = 0

    def toggle_sql_expanded(self):
        self.sql_expanded = not self.sql_expanded

    def table_next_page(self):
        max_page = max(0, (len(self.rows) - 1) // self._PAGE_SIZE)
        if self.table_page < max_page:
            self.table_page += 1

    def table_prev_page(self):
        if self.table_page > 0:
            self.table_page -= 1

    @rx.var
    def csv_data(self) -> str:
        """Build CSV string from current data for client-side download."""
        if not self.columns or not self.rows:
            return ""
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(self.columns)
        writer.writerows(self.rows)
        return output.getvalue()

    @rx.var
    def has_data(self) -> bool:
        return len(self.rows) > 0

    @rx.var
    def sorted_rows(self) -> list[list[str]]:
        """Return rows sorted by current sort column."""
        if not self.sort_column or self.sort_column not in self.columns:
            return self.rows
        idx = self.columns.index(self.sort_column)
        try:
            # Try numeric sort first
            return sorted(
                self.rows,
                key=lambda r: float(r[idx]) if idx < len(r) and r[idx] else 0,
                reverse=not self.sort_ascending,
            )
        except (ValueError, TypeError):
            return sorted(
                self.rows,
                key=lambda r: r[idx] if idx < len(r) else "",
                reverse=not self.sort_ascending,
            )

    @rx.var
    def display_rows(self) -> list[list[str]]:
        """Return paginated rows for display."""
        rows = self.sorted_rows
        start = self.table_page * self._PAGE_SIZE
        end = start + self._PAGE_SIZE
        return rows[start:end]

    @rx.var
    def table_page_display(self) -> str:
        total = max(1, (len(self.rows) - 1) // self._PAGE_SIZE + 1)
        return f"{self.table_page + 1}/{total}"

    @rx.var
    def has_pagination(self) -> bool:
        return len(self.rows) > self._PAGE_SIZE

    @rx.var
    def can_prev_page(self) -> bool:
        return self.table_page > 0

    @rx.var
    def can_next_page(self) -> bool:
        return (self.table_page + 1) * self._PAGE_SIZE < len(self.rows)

    @rx.var
    def is_kpi(self) -> bool:
        """Single-row result → display as KPI card."""
        return self.row_count == 1 and len(self.columns) <= 4 and len(self.rows) == 1

    @rx.var
    def kpi_items(self) -> list[list[str]]:
        """KPI items as [[label, value], ...] for single-row results."""
        if not self.rows or self.row_count != 1:
            return []
        row = self.rows[0]
        items = []
        for i, col in enumerate(self.columns):
            val = row[i] if i < len(row) else ""
            items.append([col, val])
        return items

    @rx.var
    def sort_indicator(self) -> str:
        """Arrow indicator for sorted column."""
        if not self.sort_column:
            return ""
        return " \u2191" if self.sort_ascending else " \u2193"

    @rx.var
    def execution_time_display(self) -> str:
        if self.execution_time_ms < 1000:
            return f"{self.execution_time_ms:.0f}ms"
        return f"{self.execution_time_ms / 1000:.2f}s"

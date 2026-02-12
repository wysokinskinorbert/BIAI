"""Query state for SQL viewer and data table."""

import reflex as rx


class QueryState(rx.State):
    """Manages current query state, SQL display, and data table."""

    # SQL
    current_sql: str = ""
    sql_dialect: str = ""
    generation_attempts: int = 0

    # Data table - use list[list[str]] for Reflex foreach compatibility
    columns: list[str] = []
    rows: list[list[str]] = []
    row_count: int = 0
    execution_time_ms: float = 0.0
    is_truncated: bool = False

    # Loading
    is_executing: bool = False

    # Export
    csv_data: str = ""

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
        self.rows = [[str(cell) for cell in row] for row in rows]
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
        self.csv_data = ""

    def prepare_csv_export(self):
        """Prepare CSV data for download."""
        if not self.columns or not self.rows:
            return
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(self.columns)
        writer.writerows(self.rows)
        self.csv_data = output.getvalue()

    @rx.var
    def has_data(self) -> bool:
        return len(self.rows) > 0

    @rx.var
    def display_rows(self) -> list[list[str]]:
        """Return rows for display (limited to 100)."""
        return self.rows[:100]

    @rx.var
    def execution_time_display(self) -> str:
        if self.execution_time_ms < 1000:
            return f"{self.execution_time_ms:.0f}ms"
        return f"{self.execution_time_ms / 1000:.2f}s"

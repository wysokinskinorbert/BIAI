"""Schema explorer state."""

import reflex as rx


class SchemaState(rx.State):
    """Manages database schema state for the explorer."""

    # Schema data - use dict[str, str] for Reflex foreach compatibility
    tables: list[dict[str, str]] = []
    selected_table: str = ""
    selected_columns: list[dict[str, str]] = []

    # Loading
    is_loading: bool = False
    schema_error: str = ""

    # Search
    search_query: str = ""

    def set_search_query(self, value: str):
        self.search_query = value

    def select_table(self, table_name: str):
        if self.selected_table == table_name:
            self.selected_table = ""
            self.selected_columns = []
            return
        self.selected_table = table_name
        # Find columns for selected table from stored column data
        for table in self._tables_full:
            if table.get("name") == table_name:
                self.selected_columns = table.get("columns", [])
                break

    @rx.var
    def filtered_tables(self) -> list[dict[str, str]]:
        if not self.search_query:
            return self.tables
        q = self.search_query.lower()
        return [t for t in self.tables if q in t.get("name", "").lower()]

    # Internal storage for full table data (columns nested inside)
    _tables_full: list[dict] = []

    @rx.event(background=True)
    async def refresh_schema(self):
        from biai.state.database import DBState

        async with self:
            self.is_loading = True
            self.schema_error = ""

        try:
            db_state = await self.get_state(DBState)
            connector = db_state._connector

            if not connector:
                async with self:
                    self.schema_error = "Not connected to database"
                    self.is_loading = False
                return

            from biai.db.schema_manager import SchemaManager
            manager = SchemaManager(connector)
            snapshot = await manager.get_snapshot(force_refresh=True)

            tables_flat: list[dict[str, str]] = []
            tables_full: list[dict] = []

            for table in snapshot.tables:
                cols = []
                for col in table.columns:
                    cols.append({
                        "name": col.name,
                        "data_type": col.data_type,
                    })

                # Flat version for the table list (foreach-safe)
                tables_flat.append({
                    "name": table.name,
                    "schema": table.schema_name,
                    "col_count": str(len(cols)),
                })

                # Full version with columns (for select_table lookup)
                tables_full.append({
                    "name": table.name,
                    "columns": cols,
                })

            async with self:
                self.tables = tables_flat
                self._tables_full = tables_full
                self.is_loading = False
        except Exception as e:
            async with self:
                self.schema_error = str(e)
                self.is_loading = False

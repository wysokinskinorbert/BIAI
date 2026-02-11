"""Schema explorer state."""

import reflex as rx


class SchemaState(rx.State):
    """Manages database schema state for the explorer."""

    # Schema data
    tables: list[dict] = []
    selected_table: str = ""
    selected_columns: list[dict] = []

    # Loading
    is_loading: bool = False
    schema_error: str = ""

    # Search
    search_query: str = ""

    def set_search_query(self, value: str):
        self.search_query = value

    def select_table(self, table_name: str):
        self.selected_table = table_name
        # Find columns for selected table
        for table in self.tables:
            if table.get("name") == table_name:
                self.selected_columns = table.get("columns", [])
                break

    @rx.var
    def filtered_tables(self) -> list[dict]:
        if not self.search_query:
            return self.tables
        q = self.search_query.lower()
        return [t for t in self.tables if q in t.get("name", "").lower()]

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

            tables_data = []
            for table in snapshot.tables:
                cols = []
                for col in table.columns:
                    cols.append({
                        "name": col.name,
                        "data_type": col.data_type,
                        "nullable": col.nullable,
                        "is_pk": col.is_primary_key,
                        "is_fk": col.is_foreign_key,
                    })
                tables_data.append({
                    "name": table.name,
                    "schema": table.schema_name,
                    "columns": cols,
                    "col_count": len(cols),
                })

            async with self:
                self.tables = tables_data
                self.is_loading = False
        except Exception as e:
            async with self:
                self.schema_error = str(e)
                self.is_loading = False

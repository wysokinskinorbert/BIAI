"""Schema explorer state."""

from typing import Any

import reflex as rx


# ERD layout constants
_ERD_COLS_PER_ROW = 3
_ERD_NODE_WIDTH = 240
_ERD_NODE_HEIGHT_BASE = 60
_ERD_NODE_HEIGHT_PER_COL = 22
_ERD_GAP_X = 300
_ERD_GAP_Y = 40


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

    # ERD data (serialized for React Flow)
    erd_nodes: list[dict[str, Any]] = []
    erd_edges: list[dict[str, Any]] = []

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

    @rx.var
    def has_erd(self) -> bool:
        return len(self.erd_nodes) > 0

    @rx.var
    def table_count_label(self) -> str:
        n = len(self.erd_nodes)
        return f"{n} tables" if n != 1 else "1 table"

    @rx.var
    def erd_edge_count(self) -> int:
        return len(self.erd_edges)

    @rx.var
    def erd_edge_count_label(self) -> str:
        n = len(self.erd_edges)
        return f"{n} foreign keys" if n != 1 else "1 foreign key"

    # Internal storage for full table data (columns nested inside)
    _tables_full: list[dict] = []

    def _compute_erd(self) -> None:
        """Build ERD nodes and edges from _tables_full data."""
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        table_names = {t["name"] for t in self._tables_full}

        for idx, table in enumerate(self._tables_full):
            col = idx % _ERD_COLS_PER_ROW
            row = idx // _ERD_COLS_PER_ROW
            num_cols = len(table.get("columns", []))
            node_h = _ERD_NODE_HEIGHT_BASE + num_cols * _ERD_NODE_HEIGHT_PER_COL

            # Calculate y offset based on max height of previous rows
            y_offset = row * (_ERD_NODE_HEIGHT_BASE + 10 * _ERD_NODE_HEIGHT_PER_COL + _ERD_GAP_Y)

            columns_data = []
            for c in table.get("columns", []):
                columns_data.append({
                    "name": c.get("name", ""),
                    "type": c.get("data_type", ""),
                    "isPk": c.get("is_pk", False),
                    "isFk": c.get("is_fk", False),
                })

                # Create edge for FK relationships
                fk_ref = c.get("fk_ref", "")
                if fk_ref and fk_ref in table_names:
                    edge_id = f"e-{table['name']}-{c['name']}-{fk_ref}"
                    edges.append({
                        "id": edge_id,
                        "source": table["name"],
                        "target": fk_ref,
                        "type": "smoothstep",
                        "animated": True,
                        "label": c["name"],
                        "style": {"stroke": "var(--orange-9)", "strokeWidth": 2},
                        "labelStyle": {"fill": "var(--gray-11)", "fontSize": 10},
                    })

            nodes.append({
                "id": table["name"],
                "type": "erdTable",
                "position": {
                    "x": col * _ERD_GAP_X,
                    "y": y_offset,
                },
                "data": {
                    "label": table["name"],
                    "columns": columns_data,
                },
            })

        self.erd_nodes = nodes
        self.erd_edges = edges

    @rx.event(background=True)
    async def refresh_schema(self):
        from biai.state.database import DBState
        from biai.models.connection import DBType, ConnectionConfig

        async with self:
            self.is_loading = True
            self.schema_error = ""

        try:
            # Read serialized config from DBState (not _connector which is transient)
            async with self:
                db_state = await self.get_state(DBState)
            async with db_state:
                if not db_state.is_connected:
                    async with self:
                        self.schema_error = "Not connected to database"
                        self.is_loading = False
                    return
                config = db_state._get_config()

            # Create a temporary connector from config
            if config.db_type == DBType.ORACLE:
                from biai.db.oracle import OracleConnector
                connector = OracleConnector(config)
            else:
                from biai.db.postgresql import PostgreSQLConnector
                connector = PostgreSQLConnector(config)

            await connector.connect()
            try:
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
                            "is_pk": col.is_primary_key,
                            "is_fk": col.is_foreign_key,
                            "fk_ref": col.foreign_key_ref or "",
                        })

                    tables_flat.append({
                        "name": table.name,
                        "schema": table.schema_name,
                        "col_count": str(len(cols)),
                    })

                    tables_full.append({
                        "name": table.name,
                        "columns": cols,
                    })

                async with self:
                    self.tables = tables_flat
                    self._tables_full = tables_full
                    self.selected_table = ""
                    self.selected_columns = []
                    self._compute_erd()
                    self.is_loading = False
            finally:
                await connector.disconnect()
        except Exception as e:
            async with self:
                self.schema_error = str(e)
                self.is_loading = False

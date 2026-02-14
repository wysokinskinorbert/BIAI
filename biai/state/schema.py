"""Schema explorer state with Data Explorer (profiling + glossary)."""

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

    # Search (also searches glossary descriptions)
    search_query: str = ""

    # ERD data (serialized for React Flow)
    erd_nodes: list[dict[str, Any]] = []
    erd_edges: list[dict[str, Any]] = []

    # --- Data Explorer: Profiling ---
    profiles: dict[str, dict] = {}  # table_name -> TableProfile.model_dump()
    is_profiling: bool = False
    profiling_progress: str = ""  # "Profiling table 3/10..."

    # --- Data Explorer: Business Glossary ---
    glossary: dict[str, dict] = {}  # table_name -> TableDescription.model_dump()
    is_generating_glossary: bool = False

    # --- Data Explorer: Selected table detail ---
    selected_profile: dict = {}  # ColumnProfile dicts for selected table
    selected_glossary: dict = {}  # TableDescription dict for selected table

    # Schema selector
    available_schemas: list[str] = []
    selected_schema: str = ""  # empty = default (public / USER)

    # Column data per table (serializable, for select_table event handler)
    table_columns: dict[str, list[dict[str, str]]] = {}

    def set_search_query(self, value: str):
        self.search_query = value

    def select_table(self, table_name: str):
        if self.selected_table == table_name:
            self.selected_table = ""
            self.selected_columns = []
            self.selected_profile = {}
            self.selected_glossary = {}
            return
        self.selected_table = table_name
        # Find columns for selected table from serialized table_columns
        self.selected_columns = self.table_columns.get(table_name, [])
        # Load profile and glossary for selected table
        self.selected_profile = self.profiles.get(table_name, {})
        self.selected_glossary = self.glossary.get(table_name, {})

    @rx.var
    def filtered_tables(self) -> list[dict[str, str]]:
        if not self.search_query:
            return self.tables
        q = self.search_query.lower()
        results = []
        for t in self.tables:
            name = t.get("name", "").lower()
            if q in name:
                results.append(t)
                continue
            # Search in glossary descriptions
            gl = self.glossary.get(t.get("name", ""), {})
            if gl:
                desc = gl.get("description", "").lower()
                bname = gl.get("business_name", "").lower()
                if q in desc or q in bname:
                    results.append(t)
        return results

    @rx.var
    def has_profiles(self) -> bool:
        return len(self.profiles) > 0

    @rx.var
    def has_glossary(self) -> bool:
        return len(self.glossary) > 0

    @rx.var
    def selected_table_description(self) -> str:
        """Business description of selected table from glossary."""
        return self.selected_glossary.get("description", "")

    @rx.var
    def selected_table_business_name(self) -> str:
        return self.selected_glossary.get("business_name", "")

    @rx.var
    def selected_table_domain(self) -> str:
        return self.selected_glossary.get("business_domain", "")

    @rx.var
    def selected_table_row_count(self) -> str:
        prof = self.selected_profile
        if prof:
            rc = prof.get("row_count", 0)
            if rc:
                return f"{rc:,}" if isinstance(rc, int) else str(rc)
        return ""

    @rx.var
    def selected_column_profiles(self) -> list[dict[str, str]]:
        """Column profiles for the selected table (flattened for foreach).

        Reflex 0.8.x rx.foreach requires fully typed vars — nested dicts
        like profile["stats"]["null_pct"] create Var[Any] which crashes.
        We flatten everything to dict[str, str] with pre-computed flags.
        """
        prof = self.selected_profile
        if not prof:
            return []
        # Build glossary column lookup
        gl = self.selected_glossary
        glossary_cols: dict[str, dict] = {}
        if gl:
            for gc in gl.get("columns", []):
                cname = gc.get("name", "")
                if cname:
                    glossary_cols[cname] = gc
        result: list[dict[str, str]] = []
        for cp in prof.get("column_profiles", []):
            stats = cp.get("stats", {})
            anomalies = cp.get("anomalies", [])
            top_vals = stats.get("top_values", [])
            mean_val = stats.get("mean")
            null_pct = float(stats.get("null_pct", 0.0))
            distinct = int(stats.get("distinct_count", 0))
            semantic = str(cp.get("semantic_type", "unknown"))

            # Hide mean for DATE/TIMESTAMP columns (avg of timestamps is meaningless)
            if mean_val is not None and "DATE" in semantic.upper():
                mean_val = None

            # Look up glossary description for this column
            col_name = str(cp.get("column_name", ""))
            gl_col = glossary_cols.get(col_name, {})
            col_desc = str(gl_col.get("description", "")) if gl_col else ""
            col_bname = str(gl_col.get("business_name", "")) if gl_col else ""

            flat: dict[str, str] = {
                "column_name": col_name,
                "data_type": str(cp.get("data_type", "")),
                "semantic_type": semantic.replace("SemanticType.", ""),
                "null_pct": f"{null_pct:.1f}",
                "distinct_count": str(distinct),
                "mean": f"{mean_val:.2f}" if mean_val is not None else "",
                "top_values_str": ", ".join(
                    str(tv.get("value", "")) for tv in top_vals[:10]
                ),
                "anomalies_str": " | ".join(
                    a.get("description", "") for a in anomalies
                ),
                "has_anomalies": "1" if anomalies else "",
                "show_top_values": "1" if distinct <= 10 and top_vals else "",
                "null_pct_high": "1" if null_pct > 50 else "",
                "has_nulls": "1" if null_pct > 0 else "",
                "has_mean": "1" if mean_val is not None else "",
                "business_desc": col_desc,
                "business_name": col_bname,
                "has_glossary": "1" if col_desc else "",
            }
            result.append(flat)
        return result

    @rx.var
    def selected_glossary_columns(self) -> dict:
        """Column glossary entries keyed by column name."""
        gl = self.selected_glossary
        if not gl:
            return {}
        cols = gl.get("columns", [])
        return {c.get("name", ""): c for c in cols if c.get("name")}

    @rx.var
    def schema_options(self) -> list[str]:
        """Schema list with '(Default)' prepended for the selector."""
        if not self.available_schemas:
            return []
        return ["(Default)"] + self.available_schemas

    @rx.var
    def selected_schema_display(self) -> str:
        """Display value for schema selector."""
        return self.selected_schema if self.selected_schema else "(Default)"

    @rx.var
    def has_schemas(self) -> bool:
        return len(self.available_schemas) > 0

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

    def _compute_erd(self) -> None:
        """Build ERD nodes and edges from table_columns data."""
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        table_names = set(self.table_columns.keys())

        for idx, table_name in enumerate(sorted(self.table_columns.keys())):
            cols = self.table_columns[table_name]
            col_idx = idx % _ERD_COLS_PER_ROW
            row = idx // _ERD_COLS_PER_ROW
            y_offset = row * (_ERD_NODE_HEIGHT_BASE + 10 * _ERD_NODE_HEIGHT_PER_COL + _ERD_GAP_Y)

            columns_data = []
            for c in cols:
                columns_data.append({
                    "name": c.get("name", ""),
                    "type": c.get("data_type", ""),
                    "isPk": c.get("is_pk", "") == "1",
                    "isFk": c.get("is_fk", "") == "1",
                })

                # Create edge for FK relationships
                fk_ref = c.get("fk_ref", "")
                if fk_ref and fk_ref in table_names:
                    edge_id = f"e-{table_name}-{c['name']}-{fk_ref}"
                    edges.append({
                        "id": edge_id,
                        "source": table_name,
                        "target": fk_ref,
                        "type": "smoothstep",
                        "animated": True,
                        "label": c["name"],
                        "style": {"stroke": "var(--orange-9)", "strokeWidth": 2},
                        "labelStyle": {"fill": "var(--gray-11)", "fontSize": 10},
                    })

            nodes.append({
                "id": table_name,
                "type": "erdTable",
                "position": {
                    "x": col_idx * _ERD_GAP_X,
                    "y": y_offset,
                },
                "data": {
                    "label": table_name,
                    "columns": columns_data,
                },
            })

        self.erd_nodes = nodes
        self.erd_edges = edges

    @rx.event(background=True)
    async def refresh_schemas(self):
        """Fetch available schemas/users from the database."""
        from biai.state.database import DBState
        from biai.models.connection import DBType

        try:
            async with self:
                db_state = await self.get_state(DBState)
            async with db_state:
                if not db_state.is_connected:
                    return
                config = db_state._get_config()

            if config.db_type == DBType.ORACLE:
                from biai.db.oracle import OracleConnector
                connector = OracleConnector(config)
            else:
                from biai.db.postgresql import PostgreSQLConnector
                connector = PostgreSQLConnector(config)

            await connector.connect()
            try:
                schemas = await connector.get_schemas()
                async with self:
                    self.available_schemas = schemas
            finally:
                await connector.disconnect()
        except Exception as e:
            from biai.utils.logger import get_logger
            get_logger(__name__).warning("refresh_schemas_error", error=str(e))

    def set_schema(self, schema: str):
        """Set selected schema and trigger refresh."""
        # "(Default)" maps to empty string = default schema
        self.selected_schema = "" if schema == "(Default)" else schema
        # Clear current data
        self.tables = []
        self.table_columns = {}
        self.selected_table = ""
        self.selected_columns = []
        self.profiles = {}
        self.glossary = {}
        self.selected_profile = {}
        self.selected_glossary = {}
        self.erd_nodes = []
        self.erd_edges = []
        return SchemaState.refresh_schema

    @rx.event(background=True)
    async def refresh_schema(self):
        from biai.state.database import DBState
        from biai.models.connection import DBType, ConnectionConfig

        async with self:
            self.is_loading = True
            self.schema_error = ""
            current_schema = self.selected_schema

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
                snapshot = await manager.get_snapshot(
                    schema=current_schema, force_refresh=True,
                )

                tables_flat: list[dict[str, str]] = []
                tbl_columns: dict[str, list[dict[str, str]]] = {}

                for table in snapshot.tables:
                    cols: list[dict[str, str]] = []
                    for col in table.columns:
                        cols.append({
                            "name": col.name,
                            "data_type": col.data_type,
                            "is_pk": "1" if col.is_primary_key else "",
                            "is_fk": "1" if col.is_foreign_key else "",
                            "fk_ref": col.foreign_key_ref or "",
                        })

                    tables_flat.append({
                        "name": table.name,
                        "schema": table.schema_name,
                        "col_count": str(len(cols)),
                    })

                    tbl_columns[table.name] = cols

                # Try loading cached profiles and glossary
                # Only for default schema — cache is keyed by db_name, not schema
                cached_profiles: dict[str, dict] = {}
                cached_glossary: dict[str, dict] = {}
                if not current_schema:
                    db_name = config.database or "default"
                    try:
                        from biai.ai.data_profiler import DataProfiler
                        cached = DataProfiler.load_cache(db_name)
                        if cached:
                            cached_profiles = {
                                k: v.model_dump() for k, v in cached.items()
                            }
                    except Exception:
                        pass
                    try:
                        from biai.ai.business_glossary import BusinessGlossaryGenerator
                        gl = BusinessGlossaryGenerator.load_cache(db_name)
                        if gl:
                            cached_glossary = {
                                td.name: td.model_dump() for td in gl.tables
                            }
                    except Exception:
                        pass

                # Also fetch available schemas if not yet loaded
                schemas_list: list[str] = []
                try:
                    schemas_list = await connector.get_schemas()
                except Exception:
                    pass

                async with self:
                    self.tables = tables_flat
                    self.table_columns = tbl_columns
                    self.selected_table = ""
                    self.selected_columns = []
                    self.selected_profile = {}
                    self.selected_glossary = {}
                    self.schema_error = ""
                    self.is_loading = False
                    if cached_profiles and not self.profiles:
                        self.profiles = cached_profiles
                    if cached_glossary and not self.glossary:
                        self.glossary = cached_glossary
                    if schemas_list:
                        self.available_schemas = schemas_list
                    self._compute_erd()
            finally:
                await connector.disconnect()
        except Exception as e:
            async with self:
                self.schema_error = str(e)
                self.is_loading = False

    @rx.event(background=True)
    async def run_profiling(self):
        """Profile all tables in background."""
        from biai.state.database import DBState
        from biai.models.connection import DBType
        from biai.ai.data_profiler import DataProfiler

        async with self:
            if self.is_profiling:
                return
            self.is_profiling = True
            self.profiling_progress = "Starting profiling..."

        try:
            async with self:
                db_state = await self.get_state(DBState)
            async with db_state:
                if not db_state.is_connected:
                    async with self:
                        self.is_profiling = False
                        self.profiling_progress = ""
                    return
                config = db_state._get_config()

            if config.db_type == DBType.ORACLE:
                from biai.db.oracle import OracleConnector
                connector = OracleConnector(config)
            else:
                from biai.db.postgresql import PostgreSQLConnector
                connector = PostgreSQLConnector(config)

            await connector.connect()
            try:
                profiler = DataProfiler(connector)
                from biai.db.schema_manager import SchemaManager
                manager = SchemaManager(connector)
                snapshot = await manager.get_snapshot()

                total = len(snapshot.tables)
                profiles_dict: dict[str, dict] = {}

                for idx, table in enumerate(snapshot.tables):
                    async with self:
                        self.profiling_progress = f"Profiling {table.name} ({idx + 1}/{total})..."

                    try:
                        profile = await profiler.profile_table(table)
                        profiles_dict[table.name] = profile.model_dump()
                    except Exception:
                        pass

                # Save to disk cache
                try:
                    from biai.models.profile import TableProfile as TPModel
                    tp_objs = {
                        k: TPModel.model_validate(v) for k, v in profiles_dict.items()
                    }
                    DataProfiler.save_cache(tp_objs, config.database or "default")
                except Exception:
                    pass

                async with self:
                    self.profiles = profiles_dict
                    self.profiling_progress = f"Profiled {len(profiles_dict)} tables"
            finally:
                await connector.disconnect()
        except Exception as e:
            async with self:
                self.profiling_progress = f"Profiling error: {e}"
        finally:
            async with self:
                self.is_profiling = False

    @rx.event(background=True)
    async def generate_glossary(self):
        """Generate AI business glossary in background."""
        from biai.state.database import DBState
        from biai.state.model import ModelState
        from biai.models.connection import DBType
        from biai.ai.business_glossary import BusinessGlossaryGenerator
        from biai.models.profile import TableProfile

        async with self:
            if self.is_generating_glossary:
                return
            self.is_generating_glossary = True

        try:
            async with self:
                model_state = await self.get_state(ModelState)
            async with model_state:
                ollama_host = model_state.ollama_host
                selected_model = model_state.selected_model

            profiles_raw = {}
            async with self:
                profiles_raw = self.profiles
                db_state = await self.get_state(DBState)
            async with db_state:
                if not db_state.is_connected:
                    async with self:
                        self.is_generating_glossary = False
                    return
                config_gl = db_state._get_config()

            if config_gl.db_type == DBType.ORACLE:
                from biai.db.oracle import OracleConnector
                conn_gl = OracleConnector(config_gl)
            else:
                from biai.db.postgresql import PostgreSQLConnector
                conn_gl = PostgreSQLConnector(config_gl)

            await conn_gl.connect()
            try:
                from biai.db.schema_manager import SchemaManager
                mgr_gl = SchemaManager(conn_gl)
                snapshot = await mgr_gl.get_snapshot()
            except Exception:
                await conn_gl.disconnect()
                async with self:
                    self.is_generating_glossary = False
                return

            # Convert raw profile dicts back to TableProfile objects
            profiles_obj = {}
            for tname, pdata in profiles_raw.items():
                try:
                    profiles_obj[tname] = TableProfile.model_validate(pdata)
                except Exception:
                    pass

            try:
                generator = BusinessGlossaryGenerator(
                    ollama_host=ollama_host,
                    ollama_model=selected_model,
                )
                glossary = await generator.generate(snapshot, profiles_obj or None)

                glossary_dict = {}
                for td in glossary.tables:
                    glossary_dict[td.name] = td.model_dump()

                async with self:
                    self.glossary = glossary_dict
            finally:
                await conn_gl.disconnect()
        except Exception:
            pass
        finally:
            async with self:
                self.is_generating_glossary = False

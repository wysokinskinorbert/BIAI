"""Query Builder state — visual block-based SQL composition."""

from typing import Any
import uuid

import reflex as rx

from biai.utils.logger import get_logger

logger = get_logger(__name__)


class QueryBuilderState(rx.State):
    """Manages visual query builder blocks and connections."""

    # Blocks: list of {id, type, config, position}
    blocks: list[dict[str, Any]] = []

    # Connections: list of {id, source, target}
    connections: list[dict[str, Any]] = []

    # Generated SQL
    generated_sql: str = ""

    # Preview result
    preview_rows: list[list] = []
    preview_columns: list[str] = []
    preview_error: str = ""
    is_previewing: bool = False

    # Block types available
    block_types: list[dict[str, str]] = [
        {"type": "table", "label": "Table", "icon": "table-2", "color": "#5470c6"},
        {"type": "filter", "label": "Filter", "icon": "filter", "color": "#91cc75"},
        {"type": "aggregate", "label": "Aggregate", "icon": "calculator", "color": "#fac858"},
        {"type": "join", "label": "Join", "icon": "git-merge", "color": "#ee6666"},
        {"type": "sort", "label": "Sort", "icon": "arrow-up-down", "color": "#73c0de"},
        {"type": "limit", "label": "Limit", "icon": "hash", "color": "#3ba272"},
    ]

    # Node selection for config editing
    selected_block_id: str = ""

    def set_selected_block_id(self, value: str):
        self.selected_block_id = value

    def add_block(self, block_type: str):
        """Add a new block to the canvas."""
        block_id = f"blk-{uuid.uuid4().hex[:6]}"
        max_y = max((b.get("position", {}).get("y", 0) for b in self.blocks), default=0)

        colors = {
            "table": "#5470c6", "filter": "#91cc75", "aggregate": "#fac858",
            "join": "#ee6666", "sort": "#73c0de", "limit": "#3ba272",
        }

        block = {
            "id": block_id,
            "type": block_type,
            "config": self._default_config(block_type),
            "position": {"x": 200, "y": max_y + 120},
            "color": colors.get(block_type, "#6b7280"),
        }
        self.blocks = self.blocks + [block]
        self._regenerate_sql()

    def remove_block(self, block_id: str):
        self.blocks = [b for b in self.blocks if b.get("id") != block_id]
        self.connections = [
            c for c in self.connections
            if c.get("source") != block_id and c.get("target") != block_id
        ]
        self._regenerate_sql()

    def connect_blocks(self, source: str, target: str):
        conn_id = f"conn-{source}-{target}"
        for c in self.connections:
            if c.get("id") == conn_id:
                return
        self.connections = self.connections + [{
            "id": conn_id, "source": source, "target": target,
        }]
        self._regenerate_sql()

    def update_block_config(self, block_id: str, config: dict):
        for i, b in enumerate(self.blocks):
            if b.get("id") == block_id:
                updated = b.copy()
                updated["config"] = config
                self.blocks[i] = updated
                break
        self._regenerate_sql()

    def update_selected_config_field(self, field: str, value: str):
        """Update a single config field on the selected block."""
        if not self.selected_block_id:
            return
        for i, b in enumerate(self.blocks):
            if b.get("id") == self.selected_block_id:
                updated = b.copy()
                cfg = updated.get("config", {}).copy()
                if field == "count":
                    try:
                        cfg[field] = int(value)
                    except ValueError:
                        cfg[field] = 100
                else:
                    cfg[field] = value
                updated["config"] = cfg
                self.blocks[i] = updated
                break
        self._regenerate_sql()

    def set_config_table_name(self, v: str):
        self.update_selected_config_field("table_name", v)

    def set_config_alias(self, v: str):
        self.update_selected_config_field("alias", v)

    def set_config_column(self, v: str):
        self.update_selected_config_field("column", v)

    def set_config_operator(self, v: str):
        self.update_selected_config_field("operator", v)

    def set_config_value(self, v: str):
        self.update_selected_config_field("value", v)

    def set_config_function(self, v: str):
        self.update_selected_config_field("function", v)

    def set_config_group_by(self, v: str):
        self.update_selected_config_field("group_by", v)

    def set_config_join_type(self, v: str):
        self.update_selected_config_field("join_type", v)

    def set_config_on_left(self, v: str):
        self.update_selected_config_field("on_left", v)

    def set_config_on_right(self, v: str):
        self.update_selected_config_field("on_right", v)

    def set_config_direction(self, v: str):
        self.update_selected_config_field("direction", v)

    def set_config_count(self, v: str):
        self.update_selected_config_field("count", v)

    def clear_all(self):
        self.blocks = []
        self.connections = []
        self.generated_sql = ""
        self.preview_rows = []
        self.preview_columns = []

    @staticmethod
    def _default_config(block_type: str) -> dict:
        if block_type == "table":
            return {"table_name": "", "alias": ""}
        elif block_type == "filter":
            return {"column": "", "operator": "=", "value": ""}
        elif block_type == "aggregate":
            return {"function": "COUNT", "column": "*", "group_by": ""}
        elif block_type == "join":
            return {"join_type": "INNER", "on_left": "", "on_right": ""}
        elif block_type == "sort":
            return {"column": "", "direction": "ASC"}
        elif block_type == "limit":
            return {"count": 100}
        return {}

    def _regenerate_sql(self):
        """Generate SQL from the block graph."""
        if not self.blocks:
            self.generated_sql = ""
            return

        # Find table blocks
        tables = [b for b in self.blocks if b.get("type") == "table"]
        if not tables:
            self.generated_sql = "-- No table block added"
            return

        # Build SQL parts
        from_parts = []
        where_parts = []
        group_parts = []
        order_parts = []
        select_parts = ["*"]
        limit_val = None

        for table in tables:
            cfg = table.get("config", {})
            tname = cfg.get("table_name", "")
            alias = cfg.get("alias", "")
            if tname:
                from_parts.append(f"{tname}" + (f" {alias}" if alias else ""))

        for block in self.blocks:
            bt = block.get("type", "")
            cfg = block.get("config", {})

            if bt == "filter":
                col = cfg.get("column", "")
                op = cfg.get("operator", "=")
                val = cfg.get("value", "")
                if col and val:
                    if op.upper() in ("LIKE", "ILIKE"):
                        where_parts.append(f"{col} {op} '%{val}%'")
                    else:
                        where_parts.append(f"{col} {op} '{val}'")

            elif bt == "aggregate":
                func = cfg.get("function", "COUNT")
                col = cfg.get("column", "*")
                gb = cfg.get("group_by", "")
                select_parts = [f"{func}({col}) AS {func.lower()}_{col}"]
                if gb:
                    select_parts.insert(0, gb)
                    group_parts.append(gb)

            elif bt == "join":
                jtype = cfg.get("join_type", "INNER")
                left = cfg.get("on_left", "")
                right = cfg.get("on_right", "")
                if left and right and len(from_parts) >= 2:
                    tbl = from_parts.pop()
                    from_parts.append(f"{from_parts.pop()} {jtype} JOIN {tbl} ON {left} = {right}")

            elif bt == "sort":
                col = cfg.get("column", "")
                direction = cfg.get("direction", "ASC")
                if col:
                    order_parts.append(f"{col} {direction}")

            elif bt == "limit":
                limit_val = cfg.get("count", 100)

        sql = f"SELECT {', '.join(select_parts)}"
        if from_parts:
            sql += f"\nFROM {', '.join(from_parts)}"
        if where_parts:
            sql += f"\nWHERE {' AND '.join(where_parts)}"
        if group_parts:
            sql += f"\nGROUP BY {', '.join(group_parts)}"
        if order_parts:
            sql += f"\nORDER BY {', '.join(order_parts)}"
        if limit_val:
            sql += f"\nLIMIT {limit_val}"

        self.generated_sql = sql

    @rx.var
    def blocks_display(self) -> list[dict[str, str]]:
        """Flattened block data for foreach (avoids nested dict subscripts)."""
        result: list[dict[str, str]] = []
        for b in self.blocks:
            cfg = b.get("config", {})
            bt = b.get("type", "")
            if bt == "table":
                desc = f"Table: {cfg.get('table_name', '') or '(select table)'}"
            elif bt == "filter":
                desc = f"{cfg.get('column', '')} {cfg.get('operator', '=')} {cfg.get('value', '')}"
            elif bt == "aggregate":
                desc = f"{cfg.get('function', 'COUNT')}({cfg.get('column', '*')})"
            elif bt == "join":
                desc = f"{cfg.get('join_type', 'INNER')} JOIN"
            elif bt == "sort":
                desc = f"Sort: {cfg.get('column', '')} {cfg.get('direction', 'ASC')}"
            elif bt == "limit":
                desc = f"Limit: {cfg.get('count', 100)}"
            else:
                desc = f"{bt} block"
            result.append({
                "id": str(b.get("id", "")),
                "type": str(bt),
                "description": desc,
            })
        return result

    def on_node_click(self, node: dict):
        """Select a block for config editing."""
        self.selected_block_id = node.get("id", "")

    def on_connect(self, params: dict):
        """Handle new connection from React Flow canvas."""
        source = params.get("source", "")
        target = params.get("target", "")
        if source and target:
            self.connect_blocks(source, target)

    def on_nodes_change(self, changes: list[dict]):
        """Persist node position after drag."""
        for change in changes:
            if change.get("type") == "position" and not change.get("dragging", True):
                node_id = change.get("id", "")
                position = change.get("position")
                if node_id and position:
                    for i, b in enumerate(self.blocks):
                        if b.get("id") == node_id:
                            updated = b.copy()
                            updated["position"] = position
                            self.blocks[i] = updated
                            break

    @rx.var
    def flow_nodes(self) -> list[dict[str, Any]]:
        """Convert blocks to React Flow nodes."""
        nodes = []
        for b in self.blocks:
            node_type = b.get("type", "table") + "Block"
            nodes.append({
                "id": b.get("id", ""),
                "type": node_type,
                "position": b.get("position", {"x": 200, "y": 0}),
                "data": {
                    "label": b.get("type", "").capitalize(),
                    "config": b.get("config", {}),
                    "color": b.get("color", "#6b7280"),
                },
            })
        return nodes

    @rx.var
    def flow_edges(self) -> list[dict[str, Any]]:
        """Convert connections to React Flow edges."""
        edges = []
        for c in self.connections:
            edges.append({
                "id": c.get("id", ""),
                "source": c.get("source", ""),
                "target": c.get("target", ""),
                "type": "smoothstep",
                "animated": True,
                "style": {"stroke": "#6b7280", "strokeWidth": 2},
            })
        return edges

    @rx.var
    def has_blocks(self) -> bool:
        return len(self.blocks) > 0

    @rx.var
    def has_sql(self) -> bool:
        return self.generated_sql != "" and not self.generated_sql.startswith("--")

    @rx.var
    def selected_block_config(self) -> dict:
        """Get config of selected block for editing."""
        for b in self.blocks:
            if b.get("id") == self.selected_block_id:
                cfg = b.get("config", {})
                return {
                    "block_type": str(b.get("type", "")),
                    "table_name": str(cfg.get("table_name", "")),
                    "alias": str(cfg.get("alias", "")),
                    "column": str(cfg.get("column", "")),
                    "operator": str(cfg.get("operator", "=")),
                    "value": str(cfg.get("value", "")),
                    "function": str(cfg.get("function", "COUNT")),
                    "group_by": str(cfg.get("group_by", "")),
                    "join_type": str(cfg.get("join_type", "INNER")),
                    "on_left": str(cfg.get("on_left", "")),
                    "on_right": str(cfg.get("on_right", "")),
                    "direction": str(cfg.get("direction", "ASC")),
                    "count": str(cfg.get("count", "100")),
                }
        return {"block_type": ""}

    @rx.var
    def has_selected_block(self) -> bool:
        return self.selected_block_id != ""

    @rx.var
    def has_preview(self) -> bool:
        return len(self.preview_columns) > 0

    @rx.var
    def preview_row_count(self) -> int:
        return len(self.preview_rows)

    def send_to_chat(self):
        """Copy generated SQL to chat input."""
        # Will be handled by cross-state in the future
        pass

    @rx.event(background=True)
    async def run_preview(self):
        """Execute generated SQL and show preview results."""
        sql = ""
        async with self:
            sql = self.generated_sql
            if not sql or sql.startswith("--"):
                self.preview_error = "No valid SQL to execute"
                return
            self.is_previewing = True
            self.preview_error = ""
            self.preview_rows = []
            self.preview_columns = []

        try:
            from biai.state.database import DBState
            from biai.db.query_executor import QueryExecutor
            from biai.models.query import QueryResult

            # Get DB connector via cross-state
            async with self:
                db_state = await self.get_state(DBState)

            connector = None
            async with db_state:
                connector = await db_state.get_connector()

            if connector is None:
                async with self:
                    self.preview_error = "Not connected to database"
                    self.is_previewing = False
                return

            # Execute with 30 row limit for preview
            executor = QueryExecutor(connector, timeout=15, row_limit=30)
            result = await executor.execute(sql)

            async with self:
                if isinstance(result, QueryResult):
                    self.preview_columns = result.columns
                    # Convert values to strings for serialization safety
                    self.preview_rows = [
                        [str(v) if v is not None else "" for v in row]
                        for row in result.rows
                    ]
                    self.preview_error = ""
                else:
                    self.preview_error = result.error_message
                    self.preview_columns = []
                    self.preview_rows = []

        except Exception as e:
            logger.error("preview_error", error=str(e))
            async with self:
                self.preview_error = str(e)
        finally:
            async with self:
                self.is_previewing = False

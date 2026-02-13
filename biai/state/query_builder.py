"""Query Builder state — visual block-based SQL composition."""

from typing import Any
import uuid

import reflex as rx


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

    def add_block(self, block_type: str):
        """Add a new block to the canvas."""
        block_id = f"blk-{uuid.uuid4().hex[:6]}"
        max_y = max((b.get("position", {}).get("y", 0) for b in self.blocks), default=0)

        block = {
            "id": block_id,
            "type": block_type,
            "config": self._default_config(block_type),
            "position": {"x": 200, "y": max_y + 120},
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

    @rx.var
    def has_blocks(self) -> bool:
        return len(self.blocks) > 0

    @rx.var
    def has_sql(self) -> bool:
        return self.generated_sql != "" and not self.generated_sql.startswith("--")

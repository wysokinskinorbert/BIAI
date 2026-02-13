"""Pinned results state for multi-query dashboard."""

import reflex as rx


class PinnedState(rx.State):
    """Manages pinned chart/table results for multi-query dashboard."""

    # Each pinned item: {id, title, engine, echarts_option, columns, rows, row_count}
    pinned_items: list[dict] = []
    show_pinned: bool = False

    def pin_current(self, title: str):
        """Pin the current chart + table result."""
        # Will be called with context from other states
        pass

    def unpin_item(self, item_id: str):
        """Remove a pinned item."""
        self.pinned_items = [p for p in self.pinned_items if p.get("id") != item_id]

    def toggle_pinned(self):
        self.show_pinned = not self.show_pinned

    def clear_all_pinned(self):
        self.pinned_items = []

    @rx.var
    def has_pinned(self) -> bool:
        return len(self.pinned_items) > 0

    @rx.var
    def pinned_count(self) -> int:
        return len(self.pinned_items)

    @rx.event(background=True)
    async def pin_current_result(self):
        """Pin current chart + data from ChartState and QueryState."""
        from biai.state.chart import ChartState
        from biai.state.query import QueryState
        import uuid

        async with self:
            chart_state = await self.get_state(ChartState)
            query_state = await self.get_state(QueryState)

        title = ""
        engine = ""
        echarts_option = {}
        columns = []
        rows = []
        row_count = 0

        async with chart_state:
            title = chart_state.chart_title
            engine = chart_state.chart_engine
            if chart_state.show_echarts:
                echarts_option = dict(chart_state.echarts_option)

        async with query_state:
            columns = list(query_state.columns)
            rows = [list(r) for r in query_state.rows[:20]]  # Max 20 rows for pinned
            row_count = query_state.row_count

        if not title and not columns:
            return

        item = {
            "id": str(uuid.uuid4())[:8],
            "title": title or "Query Result",
            "engine": engine,
            "echarts_option": echarts_option,
            "columns": columns,
            "rows": rows,
            "row_count": row_count,
        }

        async with self:
            self.pinned_items = self.pinned_items + [item]

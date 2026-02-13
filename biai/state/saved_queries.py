"""Saved queries state for favorites management."""

import reflex as rx

from biai.state.chat import ChatState


class SavedQueriesState(rx.State):
    """Manages saved/favorite queries."""

    saved_queries: list[dict] = []
    show_saved_panel: bool = False

    def load_saved_queries(self):
        """Load saved queries from disk (on_mount)."""
        from biai.utils.query_storage import QueryStorage
        self.saved_queries = QueryStorage.load_all()

    def toggle_saved_panel(self):
        self.show_saved_panel = not self.show_saved_panel

    def save_current_query(self, question: str):
        """Save a query to favorites."""
        from biai.utils.query_storage import QueryStorage
        # Get current SQL from QueryState
        sql = ""
        row_count = 0
        self.saved_queries = QueryStorage.add(question, sql, row_count)

    def delete_saved_query(self, query_id: str):
        """Delete a saved query."""
        from biai.utils.query_storage import QueryStorage
        self.saved_queries = QueryStorage.delete(query_id)

    @rx.event(background=True)
    async def run_saved_query(self, question: str):
        """Run a saved query by setting it as input and processing."""
        async with self:
            chat_state = await self.get_state(ChatState)
        async with chat_state:
            chat_state.input_value = question
            chat_state.suggested_queries = []
        async with self:
            self.show_saved_panel = False
        # Trigger message processing
        async with self:
            chat_state = await self.get_state(ChatState)
        yield ChatState.process_message

    @rx.var
    def has_saved(self) -> bool:
        return len(self.saved_queries) > 0

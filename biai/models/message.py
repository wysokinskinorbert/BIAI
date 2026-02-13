"""Chat message models."""

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Single chat message.

    Used as a schema/factory for creating message dicts.
    Reflex state stores messages as list[dict] (JSON-serializable),
    so we use ChatMessage(...).model_dump() to create validated dicts.
    """
    role: str = "assistant"
    content: str = ""
    sql: str | None = None
    has_chart: bool = False
    has_table: bool = False
    has_process: bool = False
    is_error: bool = False
    is_streaming: bool = False

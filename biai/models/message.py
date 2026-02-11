"""Chat message models."""

from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Message sender role."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Single chat message."""
    role: MessageRole
    content: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)
    sql: str | None = None
    has_chart: bool = False
    has_table: bool = False
    is_error: bool = False
    is_streaming: bool = False

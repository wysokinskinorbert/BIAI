"""Abstract base class for database connectors."""

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from biai.models.connection import ConnectionConfig
from biai.models.schema import (
    TableInfo, SchemaSnapshot, TriggerInfo, ProcedureInfo, DependencyInfo,
)
from biai.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseConnector(ABC):
    """Abstract database connector interface."""

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._connection: Any = None

    @property
    def is_connected(self) -> bool:
        return self._connection is not None

    @abstractmethod
    async def connect(self) -> None:
        """Establish database connection."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection."""

    @abstractmethod
    async def test_connection(self) -> tuple[bool, str]:
        """Test connection. Returns (success, message)."""

    @abstractmethod
    async def execute_query(self, sql: str, timeout: int = 30) -> pd.DataFrame:
        """Execute a read-only SQL query and return results as DataFrame."""

    @abstractmethod
    async def get_tables(self, schema: str = "") -> list[TableInfo]:
        """Get list of tables with column info."""

    @abstractmethod
    async def get_schema_snapshot(self, schema: str = "") -> SchemaSnapshot:
        """Get complete schema snapshot for training."""

    @abstractmethod
    async def get_schemas(self) -> list[str]:
        """Get list of available schemas/users."""

    @abstractmethod
    async def get_server_version(self) -> str:
        """Get database server version string."""

    async def get_triggers(self, schema: str = "") -> list[TriggerInfo]:
        """Get triggers on tables. Override in subclasses for DB-specific logic."""
        return []

    async def get_procedures(self, schema: str = "") -> list[ProcedureInfo]:
        """Get stored procedures/functions. Override in subclasses."""
        return []

    async def get_dependencies(self, schema: str = "") -> list[DependencyInfo]:
        """Get object dependencies (proc→table). Override in subclasses."""
        return []

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

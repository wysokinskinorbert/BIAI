"""Database connection models."""

from enum import Enum
from pydantic import BaseModel, Field


class DBType(str, Enum):
    """Supported database types."""
    ORACLE = "oracle"
    POSTGRESQL = "postgresql"


class ConnectionConfig(BaseModel):
    """Database connection configuration."""
    db_type: DBType
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(default="")
    username: str = Field(default="")
    password: str = Field(default="")
    dsn: str = Field(default="")

    @property
    def display_name(self) -> str:
        if self.dsn:
            return f"{self.db_type.value}://{self.dsn[:30]}..."
        return f"{self.db_type.value}://{self.host}:{self.port}/{self.database}"

    def get_oracle_dsn(self) -> str:
        if self.dsn:
            return self.dsn
        return f"{self.host}:{self.port}/{self.database}"

    def get_postgresql_dsn(self) -> str:
        if self.dsn:
            return self.dsn
        return (
            f"postgresql://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


class DBConnection(BaseModel):
    """Active database connection info."""
    config: ConnectionConfig
    is_connected: bool = False
    server_version: str = ""
    current_schema: str = ""

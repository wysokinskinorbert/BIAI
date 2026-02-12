"""Application settings using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

from biai.config.constants import DEFAULT_MODEL


class AppSettings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Ollama
    ollama_host: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default=DEFAULT_MODEL)

    # ChromaDB
    chroma_host: str = Field(default="http://localhost:8000")
    chroma_collection: str = Field(default="biai_schema")

    # Oracle
    oracle_dsn: str = Field(default="")
    oracle_user: str = Field(default="")
    oracle_password: str = Field(default="")

    # PostgreSQL
    postgresql_dsn: str = Field(default="")

    # Security
    encryption_key: str = Field(default="")

    # App
    app_debug: bool = Field(default=False)
    app_log_level: str = Field(default="INFO")
    query_timeout: int = Field(default=30)
    query_row_limit: int = Field(default=10_000)


def get_settings() -> AppSettings:
    """Get cached settings instance."""
    return AppSettings()

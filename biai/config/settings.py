"""Application settings using pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

from biai.config.constants import (
    DEFAULT_MODEL, DEFAULT_OLLAMA_HOST, DEFAULT_CHROMA_HOST,
    DEFAULT_CHROMA_COLLECTION, DEFAULT_NLG_MODEL, QUERY_TIMEOUT, ROW_LIMIT,
)

# Project root — directory containing rxconfig.py
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"


class AppSettings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Ollama
    ollama_host: str = Field(default=DEFAULT_OLLAMA_HOST)
    ollama_model: str = Field(default=DEFAULT_MODEL)
    ollama_sql_model: str = Field(default="")
    ollama_nlg_model: str = Field(default=DEFAULT_NLG_MODEL)

    # ChromaDB
    chroma_host: str = Field(default=DEFAULT_CHROMA_HOST)
    chroma_collection: str = Field(default=DEFAULT_CHROMA_COLLECTION)

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
    query_timeout: int = Field(default=QUERY_TIMEOUT)
    query_row_limit: int = Field(default=ROW_LIMIT)
    response_language: str = Field(default="pl")
    language_enforcement_mode: str = Field(default="strict")


def get_settings() -> AppSettings:
    """Get cached settings instance."""
    settings = AppSettings()
    if not settings.ollama_sql_model:
        settings.ollama_sql_model = settings.ollama_model or DEFAULT_MODEL
    if not settings.ollama_nlg_model:
        settings.ollama_nlg_model = DEFAULT_NLG_MODEL
    return settings


def save_env_setting(key: str, value: str) -> None:
    """Save a KEY=VALUE pair to the project .env file.

    Updates existing key or appends new one. Preserves all other lines.
    """
    lines: list[str] = []
    found = False

    if _ENV_PATH.exists():
        lines = _ENV_PATH.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(f"{key}=") or stripped.startswith(f"{key} ="):
                lines[i] = f"{key}={value}"
                found = True
                break

    if not found:
        lines.append(f"{key}={value}")

    _ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

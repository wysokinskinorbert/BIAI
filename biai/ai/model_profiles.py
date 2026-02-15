"""DB-dialect aware model profile suggestions."""

from __future__ import annotations

from dataclasses import dataclass

from biai.config.settings import get_settings


@dataclass(frozen=True)
class ModelProfile:
    """Suggested model profile metadata for a database dialect."""

    db_type: str
    label: str
    suggested_model: str
    description: str


def get_model_profile(db_type: str) -> ModelProfile:
    """Return the model profile suggestion for a selected connector type."""
    db = (db_type or "").strip().lower()
    settings = get_settings()
    shared_model = settings.ollama_sql_model or settings.ollama_model

    if db == "oracle":
        return ModelProfile(
            db_type="oracle",
            label="Oracle",
            suggested_model=shared_model,
            description="Suggested SQL profile for Oracle dialect.",
        )

    return ModelProfile(
        db_type="postgresql",
        label="PostgreSQL",
        suggested_model=shared_model,
        description="Suggested SQL profile for PostgreSQL dialect.",
    )

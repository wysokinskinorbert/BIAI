"""JSON-based connection preset storage (~/.biai/connections.json)."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

_BIAI_DIR = Path.home() / ".biai"
_STORAGE_FILE = _BIAI_DIR / "connections.json"


class ConnectionStorage:
    """CRUD operations for connection presets."""

    @staticmethod
    def load_all() -> list[dict]:
        """Load all presets from disk."""
        if not _STORAGE_FILE.exists():
            return []
        try:
            data = json.loads(_STORAGE_FILE.read_text(encoding="utf-8"))
            return data.get("presets", [])
        except (json.JSONDecodeError, Exception):
            return []

    @staticmethod
    def save_all(presets: list[dict]):
        """Save all presets to disk."""
        _BIAI_DIR.mkdir(parents=True, exist_ok=True)
        data = {"version": 1, "presets": presets}
        _STORAGE_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @staticmethod
    def add(preset: dict) -> list[dict]:
        """Add a new preset. Returns updated list."""
        presets = ConnectionStorage.load_all()
        now = datetime.now(timezone.utc).isoformat()
        preset["id"] = uuid.uuid4().hex[:8]
        preset["created_at"] = now
        preset["updated_at"] = now
        presets.append(preset)
        ConnectionStorage.save_all(presets)
        return presets

    @staticmethod
    def update(preset_id: str, updated: dict) -> list[dict]:
        """Update a preset by id. Returns updated list."""
        presets = ConnectionStorage.load_all()
        for p in presets:
            if p["id"] == preset_id:
                p.update(updated)
                p["updated_at"] = datetime.now(timezone.utc).isoformat()
                break
        ConnectionStorage.save_all(presets)
        return presets

    @staticmethod
    def delete(preset_id: str) -> list[dict]:
        """Delete a preset by id. Returns updated list."""
        presets = ConnectionStorage.load_all()
        presets = [p for p in presets if p["id"] != preset_id]
        ConnectionStorage.save_all(presets)
        return presets

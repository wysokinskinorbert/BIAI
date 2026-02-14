"""JSON-based dashboard storage (~/.biai/dashboards/)."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

_BIAI_DIR = Path.home() / ".biai"
_DASHBOARDS_DIR = _BIAI_DIR / "dashboards"
_DEFAULT_FILE = _DASHBOARDS_DIR / "_default.txt"


class DashboardStorage:
    """CRUD operations for saved dashboards."""

    @staticmethod
    def save(name: str, widgets: list[dict], layout: list[dict]):
        """Save dashboard to ~/.biai/dashboards/{name}.json."""
        _DASHBOARDS_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = name.replace(" ", "_").lower()[:50]
        path = _DASHBOARDS_DIR / f"{safe_name}.json"
        data = {
            "version": 1,
            "name": name,
            "widgets": widgets,
            "layout": layout,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    @staticmethod
    def load(name: str) -> dict | None:
        """Load dashboard by name."""
        safe_name = name.replace(" ", "_").lower()[:50]
        path = _DASHBOARDS_DIR / f"{safe_name}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            return None

    @staticmethod
    def list_dashboards() -> list[dict]:
        """List all saved dashboards."""
        if not _DASHBOARDS_DIR.exists():
            return []
        dashboards = []
        for path in sorted(_DASHBOARDS_DIR.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                dashboards.append({
                    "name": data.get("name", path.stem),
                    "file": path.stem,
                    "widget_count": len(data.get("widgets", [])),
                    "updated_at": data.get("updated_at", ""),
                })
            except Exception:
                pass
        return dashboards

    @staticmethod
    def delete(name: str) -> bool:
        safe_name = name.replace(" ", "_").lower()[:50]
        path = _DASHBOARDS_DIR / f"{safe_name}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    @staticmethod
    def get_default() -> str:
        """Return name of default dashboard (empty string if none)."""
        if not _DEFAULT_FILE.exists():
            return ""
        try:
            return _DEFAULT_FILE.read_text(encoding="utf-8").strip()
        except Exception:
            return ""

    @staticmethod
    def set_default(name: str):
        """Set or clear the default dashboard name."""
        _DASHBOARDS_DIR.mkdir(parents=True, exist_ok=True)
        if name:
            _DEFAULT_FILE.write_text(name.strip(), encoding="utf-8")
        elif _DEFAULT_FILE.exists():
            _DEFAULT_FILE.unlink()

    @staticmethod
    def generate_widget_id() -> str:
        return str(uuid.uuid4())[:8]

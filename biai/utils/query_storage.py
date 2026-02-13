"""JSON-based saved query storage (~/.biai/saved_queries.json)."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

_BIAI_DIR = Path.home() / ".biai"
_STORAGE_FILE = _BIAI_DIR / "saved_queries.json"


class QueryStorage:
    """CRUD operations for saved queries."""

    @staticmethod
    def load_all() -> list[dict]:
        if not _STORAGE_FILE.exists():
            return []
        try:
            data = json.loads(_STORAGE_FILE.read_text(encoding="utf-8"))
            return data.get("queries", [])
        except (json.JSONDecodeError, Exception):
            return []

    @staticmethod
    def save_all(queries: list[dict]):
        _BIAI_DIR.mkdir(parents=True, exist_ok=True)
        data = {"version": 1, "queries": queries}
        _STORAGE_FILE.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    @staticmethod
    def add(question: str, sql: str, row_count: int) -> list[dict]:
        queries = QueryStorage.load_all()
        # Deduplicate by question text
        for q in queries:
            if q.get("question", "").strip().lower() == question.strip().lower():
                q["sql"] = sql
                q["row_count"] = row_count
                q["updated_at"] = datetime.now(timezone.utc).isoformat()
                QueryStorage.save_all(queries)
                return queries
        queries.insert(0, {
            "id": str(uuid.uuid4())[:8],
            "question": question,
            "sql": sql,
            "row_count": row_count,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        # Keep max 50 saved queries
        queries = queries[:50]
        QueryStorage.save_all(queries)
        return queries

    @staticmethod
    def delete(query_id: str) -> list[dict]:
        queries = [q for q in QueryStorage.load_all() if q.get("id") != query_id]
        QueryStorage.save_all(queries)
        return queries

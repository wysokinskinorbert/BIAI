"""Tests for LLM helper and context documentation."""

import json
import time
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from biai.ai.llm_helper import LLMHelper, _parse_json
from biai.db.dialect import DialectHelper
from biai.models.schema import SchemaSnapshot, TableInfo, ColumnInfo


# ---------------------------------------------------------------------------
# Parse JSON tests
# ---------------------------------------------------------------------------

class TestParseJson:

    def test_direct_json(self):
        assert _parse_json('{"key": "value"}') == {"key": "value"}

    def test_markdown_fence(self):
        text = '```json\n{"key": "value"}\n```'
        assert _parse_json(text) == {"key": "value"}

    def test_embedded_json(self):
        text = 'Here is the result: {"key": "value"} and more text'
        assert _parse_json(text) == {"key": "value"}

    def test_invalid_returns_empty(self):
        assert _parse_json("not json at all") == {}

    def test_empty_returns_empty(self):
        assert _parse_json("") == {}


# ---------------------------------------------------------------------------
# LLM Helper cache tests
# ---------------------------------------------------------------------------

class TestLLMHelperCache:

    def test_write_and_read_cache(self):
        with TemporaryDirectory() as tmpdir:
            helper = LLMHelper(cache_dir=Path(tmpdir))
            helper._write_cache("test_key", {"result": 42})
            cached = helper._read_cache("test_key", ttl=3600)
            assert cached == {"result": 42}

    def test_cache_expired(self):
        with TemporaryDirectory() as tmpdir:
            helper = LLMHelper(cache_dir=Path(tmpdir))
            helper._write_cache("old_key", {"result": 1})
            # Manually set old timestamp
            path = helper._cache_path("old_key")
            data = json.loads(path.read_text())
            data["_ts"] = time.time() - 7200  # 2 hours ago
            path.write_text(json.dumps(data))
            assert helper._read_cache("old_key", ttl=3600) is None

    def test_cache_miss(self):
        with TemporaryDirectory() as tmpdir:
            helper = LLMHelper(cache_dir=Path(tmpdir))
            assert helper._read_cache("nonexistent", ttl=3600) is None

    def test_clear_cache(self):
        with TemporaryDirectory() as tmpdir:
            helper = LLMHelper(cache_dir=Path(tmpdir))
            helper._write_cache("k1", {"a": 1})
            helper._write_cache("k2", {"b": 2})
            count = helper.clear_cache()
            assert count == 2
            assert helper._read_cache("k1", ttl=3600) is None


# ---------------------------------------------------------------------------
# Context documentation tests
# ---------------------------------------------------------------------------

def _make_schema(num_tables: int = 5) -> SchemaSnapshot:
    """Create a test schema with specified number of tables."""
    tables = []
    for i in range(num_tables):
        cols = [
            ColumnInfo(name="id", data_type="INTEGER", is_primary_key=True),
            ColumnInfo(name="name", data_type="VARCHAR(100)"),
        ]
        if i > 0:
            cols.append(ColumnInfo(
                name="parent_id", data_type="INTEGER",
                is_foreign_key=True, foreign_key_ref=f"table_{i-1}.id",
            ))
        tables.append(TableInfo(name=f"table_{i}", columns=cols))
    return SchemaSnapshot(tables=tables, schema_name="test_schema")


class TestDialectDocumentationLevels:

    def test_full_includes_columns(self):
        schema = _make_schema(3)
        docs = DialectHelper.get_documentation(schema, detail_level="full")
        text = " ".join(docs)
        assert "id (INTEGER)" in text
        assert "name (VARCHAR(100))" in text

    def test_overview_no_columns(self):
        schema = _make_schema(3)
        docs = DialectHelper.get_documentation(schema, detail_level="overview")
        text = " ".join(docs)
        assert "table_0" in text
        assert "table_1" in text
        # Overview should NOT include column details
        assert "id (INTEGER)" not in text

    def test_relevant_includes_only_specified_tables(self):
        schema = _make_schema(5)
        docs = DialectHelper.get_documentation(
            schema, detail_level="relevant",
            relevant_tables=["table_1", "table_3"],
        )
        text = " ".join(docs)
        # Overview part should list all tables
        assert "table_0" in text
        # Relevant tables should have column details
        assert "Table test_schema.table_1 has columns:" in text
        assert "Table test_schema.table_3 has columns:" in text
        # Non-relevant tables should NOT have column details
        assert "Table test_schema.table_0 has columns:" not in text
        assert "Table test_schema.table_2 has columns:" not in text

    def test_empty_schema_all_levels(self):
        empty = SchemaSnapshot(tables=[])
        for level in ("full", "overview", "relevant"):
            assert DialectHelper.get_documentation(empty, detail_level=level) == []

    def test_overview_smaller_than_full(self):
        schema = _make_schema(20)
        full = DialectHelper.get_documentation(schema, detail_level="full")
        overview = DialectHelper.get_documentation(schema, detail_level="overview")
        assert len(" ".join(overview)) < len(" ".join(full))

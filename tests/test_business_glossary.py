"""Tests for BusinessGlossaryGenerator — parsing, fallback, caching."""

import json
from pathlib import Path

import pytest

from biai.ai.business_glossary import BusinessGlossaryGenerator
from biai.models.glossary import BusinessGlossary, TableDescription, ColumnDescription
from biai.models.schema import SchemaSnapshot, TableInfo, ColumnInfo


@pytest.fixture
def sample_schema():
    """Minimal schema for testing."""
    return SchemaSnapshot(
        db_type="postgresql",
        tables=[
            TableInfo(
                name="customers",
                schema_name="public",
                columns=[
                    ColumnInfo(name="id", data_type="integer", is_primary_key=True),
                    ColumnInfo(name="email", data_type="varchar"),
                    ColumnInfo(name="first_name", data_type="varchar"),
                    ColumnInfo(name="ltv", data_type="numeric"),
                ],
            ),
            TableInfo(
                name="orders",
                schema_name="public",
                columns=[
                    ColumnInfo(name="id", data_type="integer", is_primary_key=True),
                    ColumnInfo(name="customer_id", data_type="integer", is_foreign_key=True),
                    ColumnInfo(name="total_amount", data_type="numeric"),
                    ColumnInfo(name="status", data_type="varchar"),
                ],
            ),
        ],
    )


@pytest.fixture
def generator():
    return BusinessGlossaryGenerator()


class TestParseResponse:
    """Test _parse_response() JSON parsing."""

    def test_parse_valid_json(self, generator, sample_schema):
        raw = json.dumps({
            "tables": [
                {
                    "name": "customers",
                    "description": "Customer records",
                    "business_name": "Customer Database",
                    "business_domain": "Customer",
                    "columns": [
                        {
                            "name": "id",
                            "description": "Unique customer identifier",
                            "business_name": "Customer ID",
                            "examples": "1, 2, 3...",
                        },
                        {
                            "name": "ltv",
                            "description": "Lifetime Value of the customer",
                            "business_name": "Lifetime Value",
                            "examples": "1500.00, 2300.50",
                        },
                    ],
                }
            ]
        })
        result = generator._parse_response(raw, sample_schema)
        assert isinstance(result, BusinessGlossary)
        assert len(result.tables) == 1
        assert result.tables[0].name == "customers"
        assert result.tables[0].business_domain == "Customer"
        assert len(result.tables[0].columns) == 2
        assert result.tables[0].columns[1].business_name == "Lifetime Value"

    def test_parse_json_in_markdown_block(self, generator, sample_schema):
        raw = """Here is the glossary:

```json
{
  "tables": [
    {
      "name": "orders",
      "description": "Order records",
      "business_name": "Orders",
      "business_domain": "Sales",
      "columns": []
    }
  ]
}
```
"""
        result = generator._parse_response(raw, sample_schema)
        assert len(result.tables) == 1
        assert result.tables[0].name == "orders"

    def test_parse_invalid_json_raises(self, generator, sample_schema):
        with pytest.raises(Exception):
            generator._parse_response("not json at all", sample_schema)

    def test_parse_empty_tables(self, generator, sample_schema):
        raw = json.dumps({"tables": []})
        result = generator._parse_response(raw, sample_schema)
        assert len(result.tables) == 0


class TestFallbackGlossary:
    """Test _fallback_glossary() when LLM is unavailable."""

    def test_fallback_generates_all_tables(self, sample_schema):
        result = BusinessGlossaryGenerator._fallback_glossary(sample_schema)
        assert isinstance(result, BusinessGlossary)
        assert len(result.tables) == 2
        table_names = {t.name for t in result.tables}
        assert table_names == {"customers", "orders"}

    def test_fallback_business_names_title_case(self, sample_schema):
        result = BusinessGlossaryGenerator._fallback_glossary(sample_schema)
        customers = next(t for t in result.tables if t.name == "customers")
        assert customers.business_name == "Customers"

    def test_fallback_columns_included(self, sample_schema):
        result = BusinessGlossaryGenerator._fallback_glossary(sample_schema)
        customers = next(t for t in result.tables if t.name == "customers")
        col_names = {c.name for c in customers.columns}
        assert col_names == {"id", "email", "first_name", "ltv"}

    def test_fallback_column_names_title_case(self, sample_schema):
        result = BusinessGlossaryGenerator._fallback_glossary(sample_schema)
        customers = next(t for t in result.tables if t.name == "customers")
        ltv_col = next(c for c in customers.columns if c.name == "ltv")
        assert ltv_col.business_name == "Ltv"

    def test_fallback_underscore_table(self):
        schema = SchemaSnapshot(
            db_type="postgresql",
            tables=[
                TableInfo(
                    name="order_items",
                    schema_name="public",
                    columns=[ColumnInfo(name="id", data_type="integer")],
                ),
            ],
        )
        result = BusinessGlossaryGenerator._fallback_glossary(schema)
        assert result.tables[0].business_name == "Order Items"


class TestGlossaryCaching:
    """Test save/load cache for glossary."""

    def test_save_and_load(self, tmp_path, monkeypatch):
        monkeypatch.setattr("biai.ai.business_glossary._BIAI_DIR", tmp_path)

        glossary = BusinessGlossary(
            db_name="test_db",
            tables=[
                TableDescription(
                    name="customers",
                    description="All customers",
                    business_name="Customer Database",
                    business_domain="Customer",
                    columns=[
                        ColumnDescription(
                            name="id",
                            description="Primary key",
                            business_name="Customer ID",
                        ),
                    ],
                ),
            ],
            generated_at="2025-01-01T00:00:00Z",
        )

        BusinessGlossaryGenerator._save_cache(glossary)

        cache_path = tmp_path / "glossary_test_db.json"
        assert cache_path.exists()

        loaded = BusinessGlossaryGenerator.load_cache("test_db")
        assert loaded is not None
        assert loaded.db_name == "test_db"
        assert len(loaded.tables) == 1
        assert loaded.tables[0].name == "customers"
        assert loaded.tables[0].columns[0].business_name == "Customer ID"

    def test_load_missing_cache(self, tmp_path, monkeypatch):
        monkeypatch.setattr("biai.ai.business_glossary._BIAI_DIR", tmp_path)
        result = BusinessGlossaryGenerator.load_cache("nonexistent")
        assert result is None

    def test_load_corrupted_cache(self, tmp_path, monkeypatch):
        monkeypatch.setattr("biai.ai.business_glossary._BIAI_DIR", tmp_path)
        path = tmp_path / "glossary_bad.json"
        path.write_text("{broken json", encoding="utf-8")
        result = BusinessGlossaryGenerator.load_cache("bad")
        assert result is None

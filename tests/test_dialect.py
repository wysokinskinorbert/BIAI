"""Tests for dialect helpers."""

import pytest

from biai.db.dialect import DialectHelper
from biai.models.connection import DBType


class TestDialectHelper:
    def test_oracle_rules_contain_fetch_first(self):
        rules = DialectHelper.get_rules(DBType.ORACLE)
        assert any("FETCH FIRST" in r for r in rules)

    def test_postgresql_rules_contain_limit(self):
        rules = DialectHelper.get_rules(DBType.POSTGRESQL)
        assert any("LIMIT" in r for r in rules)

    def test_oracle_dialect_name(self):
        assert DialectHelper.get_dialect_name(DBType.ORACLE) == "oracle"

    def test_postgresql_dialect_name(self):
        assert DialectHelper.get_dialect_name(DBType.POSTGRESQL) == "postgres"

    def test_oracle_sqlglot_dialect(self):
        assert DialectHelper.get_sqlglot_dialect(DBType.ORACLE) == "oracle"

    def test_generate_examples_from_schema(self, sample_schema):
        examples = DialectHelper.get_examples(DBType.POSTGRESQL, schema=sample_schema)
        assert len(examples) > 0
        assert all(isinstance(e, tuple) and len(e) == 2 for e in examples)

    def test_generate_docs_from_schema(self, sample_schema):
        docs = DialectHelper.get_documentation(sample_schema)
        assert len(docs) > 0
        assert any("customers" in d for d in docs)

    def test_empty_schema_returns_empty(self):
        assert DialectHelper.get_examples(DBType.POSTGRESQL) == []
        assert DialectHelper.get_documentation(None) == []

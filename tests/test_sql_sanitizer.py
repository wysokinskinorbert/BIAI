"""Tests for SQL sanitizer helpers."""

from biai.ai.sql_sanitizer import sanitize_generated_sql


class TestSQLSanitizer:
    def test_strips_sql_tags(self):
        raw = "<sql>SELECT * FROM customers</sql>"
        assert sanitize_generated_sql(raw) == "SELECT * FROM customers"

    def test_extracts_from_fenced_block(self):
        raw = "Result:\n```sql\nSELECT id, name FROM customers\n```"
        assert sanitize_generated_sql(raw) == "SELECT id, name FROM customers"

    def test_adds_select_for_sql_fragment(self):
        raw = "'SLA_ANALYSIS', COUNT(*) FROM V_TICKET_SLA_ANALYSIS"
        assert sanitize_generated_sql(raw).startswith("SELECT ")

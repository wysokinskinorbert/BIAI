"""Tests for self-correction loop."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from biai.ai.self_correction import SelfCorrectionLoop, _clean_sql
from biai.ai.sql_validator import SQLValidator


@pytest.fixture
def validator():
    return SQLValidator(dialect="postgres")


class TestCleanSQL:
    """Test SQL cleaning utility."""

    def test_clean_simple(self):
        assert _clean_sql("SELECT 1") == "SELECT 1"

    def test_clean_markdown_fences(self):
        raw = "```sql\nSELECT * FROM test\n```"
        assert "SELECT * FROM test" in _clean_sql(raw)

    def test_clean_sql_tags(self):
        raw = "<sql>SELECT * FROM test</sql>"
        assert _clean_sql(raw) == "SELECT * FROM test"

    def test_clean_whitespace(self):
        assert _clean_sql("  SELECT 1  ") == "SELECT 1"

    def test_clean_empty(self):
        assert _clean_sql("") == ""


class TestSelfCorrection:
    """Test self-correction loop."""

    def test_success_first_attempt(self, validator):
        mock_vanna = MagicMock()
        mock_vanna.generate_sql.return_value = "SELECT * FROM customers"

        loop = SelfCorrectionLoop(mock_vanna, validator, max_retries=3)

        import asyncio
        query, errors = asyncio.run(
            loop.generate_with_correction("Show all customers")
        )

        assert query.is_valid
        assert len(errors) == 0
        assert query.generation_attempt == 1

    def test_success_after_retry(self, validator):
        mock_vanna = MagicMock()
        # First attempt: invalid SQL, second: valid
        mock_vanna.generate_sql.side_effect = [
            "SELEC * FORM customers",  # typo - parse error
            "SELECT * FROM customers",
        ]

        loop = SelfCorrectionLoop(mock_vanna, validator, max_retries=3)

        import asyncio
        query, errors = asyncio.run(
            loop.generate_with_correction("Show all customers")
        )

        assert query.is_valid
        assert len(errors) == 1
        assert query.generation_attempt == 2

    def test_all_attempts_fail(self, validator):
        mock_vanna = MagicMock()
        mock_vanna.generate_sql.return_value = "INSERT INTO test VALUES (1)"

        loop = SelfCorrectionLoop(mock_vanna, validator, max_retries=3)

        import asyncio
        query, errors = asyncio.run(
            loop.generate_with_correction("Insert something")
        )

        assert not query.is_valid
        assert len(errors) == 3

    def test_empty_sql_generation(self, validator):
        mock_vanna = MagicMock()
        mock_vanna.generate_sql.return_value = None

        loop = SelfCorrectionLoop(mock_vanna, validator, max_retries=2)

        import asyncio
        query, errors = asyncio.run(
            loop.generate_with_correction("Something")
        )

        assert not query.is_valid
        assert len(errors) == 2

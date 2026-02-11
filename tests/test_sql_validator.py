"""Tests for SQL validator."""

import pytest
from biai.ai.sql_validator import SQLValidator


@pytest.fixture
def validator():
    return SQLValidator(dialect="postgres")


@pytest.fixture
def oracle_validator():
    return SQLValidator(dialect="oracle")


class TestSQLValidator:
    """Test SQL validation (read-only enforcement)."""

    def test_valid_select(self, validator):
        result = validator.validate("SELECT * FROM customers")
        assert result.is_valid
        assert result.validation_error is None

    def test_valid_select_with_where(self, validator):
        result = validator.validate(
            "SELECT name, email FROM customers WHERE id = 1"
        )
        assert result.is_valid

    def test_valid_select_with_join(self, validator):
        result = validator.validate(
            "SELECT c.name, o.amount FROM customers c "
            "JOIN orders o ON c.id = o.customer_id"
        )
        assert result.is_valid

    def test_valid_aggregate(self, validator):
        result = validator.validate(
            "SELECT customer_id, SUM(amount) as total "
            "FROM orders GROUP BY customer_id ORDER BY total DESC"
        )
        assert result.is_valid

    def test_valid_subquery(self, validator):
        result = validator.validate(
            "SELECT * FROM customers WHERE id IN "
            "(SELECT customer_id FROM orders WHERE amount > 100)"
        )
        assert result.is_valid

    def test_valid_limit(self, validator):
        result = validator.validate(
            "SELECT * FROM customers LIMIT 10"
        )
        assert result.is_valid

    # Blocked operations
    def test_block_insert(self, validator):
        result = validator.validate(
            "INSERT INTO customers (name) VALUES ('hacker')"
        )
        assert not result.is_valid
        assert "INSERT" in result.validation_error

    def test_block_update(self, validator):
        result = validator.validate(
            "UPDATE customers SET name = 'hacked' WHERE id = 1"
        )
        assert not result.is_valid

    def test_block_delete(self, validator):
        result = validator.validate(
            "DELETE FROM customers WHERE id = 1"
        )
        assert not result.is_valid

    def test_block_drop(self, validator):
        result = validator.validate("DROP TABLE customers")
        assert not result.is_valid

    def test_block_alter(self, validator):
        result = validator.validate(
            "ALTER TABLE customers ADD COLUMN phone VARCHAR(20)"
        )
        assert not result.is_valid

    def test_block_truncate(self, validator):
        result = validator.validate("TRUNCATE TABLE customers")
        assert not result.is_valid

    # Injection patterns
    def test_block_multiple_statements(self, validator):
        result = validator.validate(
            "SELECT * FROM customers; DROP TABLE customers"
        )
        assert not result.is_valid

    def test_block_comment_injection(self, validator):
        result = validator.validate(
            "SELECT * FROM customers -- WHERE id = 1"
        )
        assert not result.is_valid

    def test_block_dbms_calls(self, validator):
        result = validator.validate(
            "SELECT DBMS_OUTPUT.PUT_LINE('hello') FROM DUAL"
        )
        assert not result.is_valid

    # Edge cases
    def test_empty_sql(self, validator):
        result = validator.validate("")
        assert not result.is_valid

    def test_strips_semicolon(self, validator):
        result = validator.validate("SELECT 1;")
        assert result.is_valid
        assert result.sql == "SELECT 1"

    def test_strips_whitespace(self, validator):
        result = validator.validate("  SELECT 1  ")
        assert result.is_valid

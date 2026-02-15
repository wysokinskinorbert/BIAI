"""Tests for SQL validator."""

import re

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

    def test_strip_comment_and_validate(self, validator):
        """Comments are stripped (AI models generate them), remaining SQL is validated."""
        result = validator.validate(
            "SELECT * FROM customers -- WHERE id = 1"
        )
        assert result.is_valid
        assert result.sql == "SELECT * FROM customers"

    def test_strip_block_comment(self, validator):
        result = validator.validate(
            "SELECT /* all customers */ * FROM customers"
        )
        assert result.is_valid

    def test_comment_stripped_reveals_safe_sql(self, validator):
        """Comment stripping removes the dangerous part, leaving safe SQL."""
        result = validator.validate(
            "SELECT * FROM customers; -- DROP TABLE customers"
        )
        # After stripping comment: "SELECT * FROM customers;" → valid single SELECT
        assert result.is_valid

    def test_real_multi_statement_injection_blocked(self, validator):
        """Actual multi-statement injection (no comment hiding) is still blocked."""
        result = validator.validate(
            "SELECT * FROM customers; DROP TABLE customers"
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

    # UNION / INTERSECT / EXCEPT (set operations)
    def test_valid_union_all(self, validator):
        result = validator.validate(
            "SELECT status, COUNT(*) FROM orders GROUP BY status "
            "UNION ALL "
            "SELECT status, COUNT(*) FROM shipments GROUP BY status"
        )
        assert result.is_valid
        assert result.validation_error is None

    def test_valid_union(self, validator):
        result = validator.validate(
            "SELECT name FROM customers "
            "UNION "
            "SELECT name FROM suppliers"
        )
        assert result.is_valid

    def test_valid_intersect(self, validator):
        result = validator.validate(
            "SELECT customer_id FROM orders "
            "INTERSECT "
            "SELECT customer_id FROM returns"
        )
        assert result.is_valid

    def test_valid_except(self, validator):
        result = validator.validate(
            "SELECT customer_id FROM orders "
            "EXCEPT "
            "SELECT customer_id FROM blacklist"
        )
        assert result.is_valid

    def test_union_with_insert_blocked(self, validator):
        """UNION with INSERT in one branch should be blocked."""
        result = validator.validate(
            "SELECT * FROM customers "
            "UNION ALL "
            "INSERT INTO customers (name) VALUES ('hacker')"
        )
        assert not result.is_valid


class TestSQLiteRewriting:
    """Test SQLite → PostgreSQL function rewriting (Arctic model generates SQLite syntax)."""

    def test_strftime_year_month(self, validator):
        result = validator.validate(
            "SELECT strftime('%Y-%m', order_date) AS month, COUNT(*) "
            "FROM orders GROUP BY strftime('%Y-%m', order_date)"
        )
        assert result.is_valid
        assert "TO_CHAR" in result.sql
        assert "strftime" not in result.sql.lower()
        assert "'YYYY-MM'" in result.sql

    def test_strftime_year(self, validator):
        result = validator.validate(
            "SELECT strftime('%Y', created_at) AS year FROM orders"
        )
        assert result.is_valid
        assert "TO_CHAR" in result.sql
        assert "'YYYY'" in result.sql

    def test_date_function(self, validator):
        result = validator.validate(
            "SELECT date(created_at) AS day, COUNT(*) FROM orders GROUP BY date(created_at)"
        )
        assert result.is_valid
        # sqlglot may transpile ::date to CAST(... AS DATE) — both are valid
        assert "::date" in result.sql or "CAST(" in result.sql
        assert not re.search(r"\bdate\(", result.sql, re.IGNORECASE)

    def test_date_now_minus_interval(self, validator):
        """DATE('now', '-1 year') → CURRENT_DATE - INTERVAL '1 year'."""
        result = validator.validate(
            "SELECT * FROM orders WHERE order_date >= DATE('now', '-1 year')"
        )
        assert result.is_valid
        assert "CURRENT_DATE" in result.sql
        assert "INTERVAL" in result.sql
        assert "date(" not in result.sql.lower()

    def test_date_now_plus_interval(self, validator):
        """DATE('now', '+3 month') → CURRENT_DATE + INTERVAL '3 month'."""
        result = validator.validate(
            "SELECT * FROM orders WHERE due_date <= DATE('now', '+3 month')"
        )
        assert result.is_valid
        assert "CURRENT_DATE +" in result.sql
        assert "interval '3 month'" in result.sql.lower()

    def test_date_now_only(self, validator):
        """DATE('now') → CURRENT_DATE."""
        result = validator.validate(
            "SELECT * FROM orders WHERE order_date = DATE('now')"
        )
        assert result.is_valid
        assert "CURRENT_DATE" in result.sql
        assert "date('now')" not in result.sql.lower()

    def test_date_now_start_of_month(self, validator):
        """DATE('now', 'start of month') → DATE_TRUNC('month', CURRENT_DATE)."""
        result = validator.validate(
            "SELECT * FROM orders WHERE order_date >= DATE('now', 'start of month')"
        )
        assert result.is_valid
        assert "DATE_TRUNC" in result.sql
        assert "CURRENT_DATE" in result.sql

    def test_no_rewrite_for_oracle(self, oracle_validator):
        """Oracle validator should NOT rewrite SQLite functions (different fix path)."""
        result = oracle_validator.validate(
            "SELECT strftime('%Y-%m', order_date) FROM orders"
        )
        # Oracle validator won't rewrite — strftime stays, may fail AST
        # but should not contain TO_CHAR from rewriting
        assert "TO_CHAR" not in (result.sql or "")

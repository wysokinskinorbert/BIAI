"""SQL dialect helpers for Oracle vs PostgreSQL."""

from biai.models.connection import DBType


class DialectHelper:
    """Provides dialect-specific SQL rules and examples."""

    ORACLE_RULES = [
        "Use FETCH FIRST N ROWS ONLY instead of LIMIT (Oracle 12c+).",
        "Use NVL() instead of COALESCE() for simple null checks.",
        "Use SYSDATE for current date, not NOW().",
        "Use TO_DATE('2024-01-01', 'YYYY-MM-DD') for date literals.",
        "Use TO_CHAR() for date formatting.",
        "Use (+) or ANSI JOIN syntax for outer joins.",
        "String comparison is case-sensitive by default.",
        "Use DUAL table for SELECT without FROM: SELECT 1 FROM DUAL.",
        "Use ROWNUM or ROW_NUMBER() OVER() for row numbering.",
        "Use || for string concatenation.",
    ]

    POSTGRESQL_RULES = [
        "Use LIMIT N OFFSET M for pagination.",
        "Use COALESCE() for null handling.",
        "Use NOW() or CURRENT_TIMESTAMP for current date/time.",
        "Use ::type for casting: '2024-01-01'::date.",
        "Use ILIKE for case-insensitive pattern matching.",
        "Use || for string concatenation.",
        "Use EXTRACT(field FROM date) for date parts.",
        "Use ARRAY_AGG() and STRING_AGG() for aggregation.",
        "Use DISTINCT ON (column) for distinct per group.",
        "Use GENERATE_SERIES() for sequence generation.",
    ]

    ORACLE_EXAMPLES = [
        (
            "Show top 10 customers by revenue",
            "SELECT customer_name, SUM(amount) AS total_revenue "
            "FROM orders GROUP BY customer_name "
            "ORDER BY total_revenue DESC FETCH FIRST 10 ROWS ONLY"
        ),
        (
            "Show monthly sales for 2024",
            "SELECT TO_CHAR(order_date, 'YYYY-MM') AS month, SUM(amount) AS total "
            "FROM orders WHERE order_date >= TO_DATE('2024-01-01', 'YYYY-MM-DD') "
            "GROUP BY TO_CHAR(order_date, 'YYYY-MM') ORDER BY month"
        ),
    ]

    POSTGRESQL_EXAMPLES = [
        (
            "Show top 10 customers by revenue",
            "SELECT customer_name, SUM(amount) AS total_revenue "
            "FROM orders GROUP BY customer_name "
            "ORDER BY total_revenue DESC LIMIT 10"
        ),
        (
            "Show monthly sales for 2024",
            "SELECT TO_CHAR(order_date, 'YYYY-MM') AS month, SUM(amount) AS total "
            "FROM orders WHERE order_date >= '2024-01-01'::date "
            "GROUP BY TO_CHAR(order_date, 'YYYY-MM') ORDER BY month"
        ),
    ]

    @classmethod
    def get_rules(cls, db_type: DBType) -> list[str]:
        if db_type == DBType.ORACLE:
            return cls.ORACLE_RULES
        return cls.POSTGRESQL_RULES

    @classmethod
    def get_examples(cls, db_type: DBType) -> list[tuple[str, str]]:
        if db_type == DBType.ORACLE:
            return cls.ORACLE_EXAMPLES
        return cls.POSTGRESQL_EXAMPLES

    @classmethod
    def get_dialect_name(cls, db_type: DBType) -> str:
        if db_type == DBType.ORACLE:
            return "oracle"
        return "postgres"

    @classmethod
    def get_sqlglot_dialect(cls, db_type: DBType) -> str:
        """Get sqlglot dialect string."""
        if db_type == DBType.ORACLE:
            return "oracle"
        return "postgres"

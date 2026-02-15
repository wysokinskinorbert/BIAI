"""SQL validation using sqlglot AST parsing."""

import re

import sqlglot
from sqlglot import exp

from biai.config.constants import BLOCKED_KEYWORDS, BLOCKED_PATTERNS
from biai.models.query import SQLQuery
from biai.utils.logger import get_logger

logger = get_logger(__name__)


class SQLValidator:
    """Validates SQL queries for safety (read-only enforcement)."""

    def __init__(self, dialect: str = ""):
        self._dialect = dialect or None

    def validate(self, sql: str) -> SQLQuery:
        """Validate a SQL query. Returns SQLQuery with is_valid flag."""
        sql = sql.strip().rstrip(";").strip()

        # Strip SQL comments (AI models often generate -- or /* */ comments)
        sql = self._strip_comments(sql)

        # Rewrite SQLite-specific functions for PostgreSQL
        if self._dialect == "postgres":
            sql = self._rewrite_sqlite_functions(sql)

        # Sanitize Oracle bind variable placeholders before validation
        if self._dialect == "oracle":
            sql = self._sanitize_bind_variables(sql)

        query = SQLQuery(sql=sql, dialect=self._dialect or "")

        # Layer 1: Check for blocked keywords (case-insensitive)
        error = self._check_blocked_keywords(sql)
        if error:
            query.validation_error = error
            logger.warning("sql_blocked_keyword", sql=sql[:100], error=error)
            return query

        # Layer 2: Check regex patterns (injection patterns)
        error = self._check_blocked_patterns(sql)
        if error:
            query.validation_error = error
            logger.warning("sql_blocked_pattern", sql=sql[:100], error=error)
            return query

        # Layer 3: AST parsing with sqlglot + transpilation
        error, transpiled = self._check_ast(sql)
        if error:
            query.validation_error = error
            logger.warning("sql_ast_invalid", sql=sql[:100], error=error)
            return query

        # Use transpiled SQL (fixes LIMIT → FETCH FIRST for Oracle, etc.)
        if transpiled and transpiled != sql:
            logger.info("sql_transpiled", original=sql[:80], transpiled=transpiled[:80])
            query.sql = transpiled

        query.is_valid = True
        logger.info("sql_validated", sql=query.sql[:100])
        return query

    def _check_blocked_keywords(self, sql: str) -> str | None:
        """Check for blocked SQL keywords."""
        upper = sql.upper()

        for keyword in BLOCKED_KEYWORDS:
            # Keywords ending with _ (like DBMS_) use prefix match
            if keyword.endswith("_"):
                if keyword in upper:
                    return f"Blocked keyword detected: {keyword}"
                continue

            # Match whole word only
            pattern = rf"\b{keyword}\b"
            if re.search(pattern, upper):
                # Special case: INTO in SELECT context can be a subquery alias
                if keyword == "INTO" and "SELECT" in upper:
                    # Block INTO OUTFILE/DUMPFILE but allow column aliases
                    if "OUTFILE" in upper or "DUMPFILE" in upper:
                        return f"Blocked keyword detected: {keyword} OUTFILE/DUMPFILE"
                    continue
                return f"Blocked keyword detected: {keyword}"
        return None

    def _check_blocked_patterns(self, sql: str) -> str | None:
        """Check for injection patterns."""
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                return f"Blocked pattern detected: {pattern}"
        return None

    def _check_ast(self, sql: str) -> tuple[str | None, str | None]:
        """Parse SQL into AST, verify it's SELECT, and transpile to target dialect.

        Returns:
            Tuple of (error_message, transpiled_sql). If error, transpiled is None.
        """
        try:
            parsed = sqlglot.parse(sql, dialect=self._dialect)
        except sqlglot.errors.ParseError as e:
            return f"SQL parse error: {e}", None

        if not parsed:
            return "Empty SQL statement", None

        if len(parsed) > 1:
            return "Multiple statements detected (only single SELECT allowed)", None

        statement = parsed[0]

        if statement is None:
            return "Failed to parse SQL statement", None

        # Must be a SELECT or set operation (UNION, INTERSECT, EXCEPT)
        _allowed_roots = (exp.Select, exp.Union, exp.Intersect, exp.Except)
        if not isinstance(statement, _allowed_roots):
            stmt_type = type(statement).__name__
            return f"Only SELECT statements allowed, got: {stmt_type}", None

        # Check for subqueries containing non-SELECT (walks entire tree including UNION branches)
        for node in statement.walk():
            if isinstance(node, (exp.Insert, exp.Update, exp.Delete, exp.Drop,
                                 exp.Create, exp.Alter)):
                return f"Non-SELECT operation found in query: {type(node).__name__}", None

        # Transpile to target dialect (e.g. LIMIT → FETCH FIRST for Oracle)
        try:
            transpiled = statement.sql(dialect=self._dialect)
        except Exception:
            transpiled = sql

        return None, transpiled

    def _strip_comments(self, sql: str) -> str:
        """Strip SQL comments from AI-generated queries.

        AI models (especially Arctic-Text2SQL) often include -- line comments
        and /* block comments */ which trigger our injection-prevention patterns.
        Stripping them is safe because the SQL comes from the AI, not user input.
        """
        # Remove block comments first (/* ... */), including multiline
        sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
        # Remove line comments (-- to end of line)
        sql = re.sub(r"--[^\n]*", "", sql)
        # Clean up extra whitespace
        sql = re.sub(r"\s+", " ", sql).strip()
        return sql

    def _rewrite_sqlite_functions(self, sql: str) -> str:
        """Rewrite SQLite-specific functions to PostgreSQL equivalents.

        Arctic-Text2SQL-R1 was fine-tuned on Spider/BIRD (SQLite) and
        generates strftime()/date() which don't exist in PostgreSQL.
        """
        # strftime('%Y-%m', col) → TO_CHAR(col, 'YYYY-MM')
        # strftime('%Y', col) → TO_CHAR(col, 'YYYY')
        # strftime('%m', col) → TO_CHAR(col, 'MM')
        _FMT_MAP = {
            "'%Y-%m'": "'YYYY-MM'",
            "'%Y'": "'YYYY'",
            "'%m'": "'MM'",
            "'%d'": "'DD'",
            "'%Y-%m-%d'": "'YYYY-MM-DD'",
            "'%H:%M'": "'HH24:MI'",
        }
        for sqlite_fmt, pg_fmt in _FMT_MAP.items():
            pattern = rf"strftime\(\s*{re.escape(sqlite_fmt)}\s*,\s*(.+?)\)"
            replacement = rf"TO_CHAR(\1, {pg_fmt})"
            sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)

        # Catch remaining strftime() calls with unknown formats
        sql = re.sub(
            r"strftime\(\s*'([^']*)'\s*,\s*(.+?)\)",
            lambda m: f"TO_CHAR({m.group(2)}, '{m.group(1)}')",
            sql,
            flags=re.IGNORECASE,
        )

        # SQLite DATE() with modifiers → PostgreSQL date arithmetic
        # DATE('now', '-1 year') → CURRENT_DATE - INTERVAL '1 year'
        # DATE('now', '+3 month') → CURRENT_DATE + INTERVAL '3 month'
        # DATE('now', 'start of month') → DATE_TRUNC('month', CURRENT_DATE)
        sql = re.sub(
            r"\bdate\(\s*'now'\s*,\s*'([+-]?)(\d+)\s+(year|month|day)s?'\s*\)",
            lambda m: (
                f"CURRENT_DATE {'-' if m.group(1) == '-' else '+'} "
                f"INTERVAL '{m.group(2)} {m.group(3)}'"
            ),
            sql,
            flags=re.IGNORECASE,
        )

        # DATE('now', 'start of month') → DATE_TRUNC('month', CURRENT_DATE)
        sql = re.sub(
            r"\bdate\(\s*'now'\s*,\s*'start of (year|month|day)'\s*\)",
            r"DATE_TRUNC('\1', CURRENT_DATE)",
            sql,
            flags=re.IGNORECASE,
        )

        # DATE('now') → CURRENT_DATE
        sql = re.sub(
            r"\bdate\(\s*'now'\s*\)",
            "CURRENT_DATE",
            sql,
            flags=re.IGNORECASE,
        )

        # date(col) → col::date (PostgreSQL cast) — single column/expression arg
        sql = re.sub(
            r"\bdate\(\s*([^()]+?)\s*\)",
            r"(\1)::date",
            sql,
            flags=re.IGNORECASE,
        )

        return sql

    def _sanitize_bind_variables(self, sql: str) -> str:
        """Replace Oracle bind variable placeholders with string literals.

        LLMs sometimes generate :PARAM_NAME which Oracle interprets as bind
        variables.  Replace them with 'PARAM_NAME' string literals so the
        query can execute without parameters.
        """
        return re.sub(r":([A-Za-z_]\w*)", r"'\1'", sql)

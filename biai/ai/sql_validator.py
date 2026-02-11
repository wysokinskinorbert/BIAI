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

        # Layer 3: AST parsing with sqlglot
        error = self._check_ast(sql)
        if error:
            query.validation_error = error
            logger.warning("sql_ast_invalid", sql=sql[:100], error=error)
            return query

        query.is_valid = True
        logger.info("sql_validated", sql=sql[:100])
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

    def _check_ast(self, sql: str) -> str | None:
        """Parse SQL into AST and verify it's a SELECT statement."""
        try:
            parsed = sqlglot.parse(sql, dialect=self._dialect)
        except sqlglot.errors.ParseError as e:
            return f"SQL parse error: {e}"

        if not parsed:
            return "Empty SQL statement"

        if len(parsed) > 1:
            return "Multiple statements detected (only single SELECT allowed)"

        statement = parsed[0]

        if statement is None:
            return "Failed to parse SQL statement"

        # Must be a SELECT expression
        if not isinstance(statement, exp.Select):
            stmt_type = type(statement).__name__
            return f"Only SELECT statements allowed, got: {stmt_type}"

        # Check for subqueries containing non-SELECT
        for node in statement.walk():
            if isinstance(node, (exp.Insert, exp.Update, exp.Delete, exp.Drop,
                                 exp.Create, exp.Alter)):
                return f"Non-SELECT operation found in query: {type(node).__name__}"

        return None

"""Self-correction loop for SQL generation."""

import re

from biai.ai.sql_validator import SQLValidator
from biai.ai.sql_sanitizer import sanitize_generated_sql
from biai.ai.prompt_templates import CORRECTION_PROMPT
from biai.config.constants import MAX_RETRIES
from biai.models.query import SQLQuery, QueryError
from biai.utils.logger import get_logger

logger = get_logger(__name__)

_REFUSAL_PATTERNS = re.compile(
    r"sorry|i can'?t|i cannot|i'?m unable|i am unable|not able to|"
    r"can'?t assist|cannot assist|cannot help|apologize|as an ai",
    re.IGNORECASE,
)


def _is_refusal(text: str) -> bool:
    """Detect if LLM output is a refusal instead of SQL."""
    stripped = text.strip()
    if stripped.upper().startswith(("SELECT", "WITH")):
        return False
    return bool(_REFUSAL_PATTERNS.search(stripped))


class SelfCorrectionLoop:
    """Retry SQL generation with error feedback (max N attempts)."""

    def __init__(self, vanna_client, validator: SQLValidator, max_retries: int = MAX_RETRIES):
        self._vanna = vanna_client
        self._validator = validator
        self._max_retries = max_retries

    async def generate_with_correction(
        self,
        question: str,
        db_executor=None,
    ) -> tuple[SQLQuery, list[str]]:
        """Generate SQL with self-correction on failure.

        Returns:
            Tuple of (final SQLQuery, list of error messages from attempts)
        """
        errors: list[str] = []
        last_sql = ""

        for attempt in range(1, self._max_retries + 1):
            logger.info("sql_generation_attempt", attempt=attempt, question=question[:50])

            # Generate SQL
            if attempt == 1 or not last_sql:
                # First attempt OR previous was refusal/empty → fresh generation
                raw_sql = self._vanna.generate_sql(question)
            else:
                # Use correction prompt with previous SQL and error
                correction = CORRECTION_PROMPT.format(
                    sql=last_sql,
                    error=errors[-1] if errors else "Unknown error",
                    dialect=self._validator._dialect or "SQL",
                )
                raw_sql = self._vanna.generate_sql(f"{question}\n\n{correction}")

            if not raw_sql:
                error_msg = f"Attempt {attempt}: Empty SQL generated"
                errors.append(error_msg)
                logger.warning("empty_sql", attempt=attempt)
                continue

            # Clean SQL (remove markdown fences if present)
            sql = _clean_sql(raw_sql)

            # Detect AI refusal (e.g. "Sorry, I can't assist...")
            if _is_refusal(sql):
                error_msg = f"Attempt {attempt}: AI refused to generate SQL"
                errors.append(error_msg)
                logger.warning("ai_refusal", attempt=attempt, response=sql[:100])
                continue

            last_sql = sql

            # Validate
            query = self._validator.validate(sql)
            query.generation_attempt = attempt

            if not query.is_valid:
                error_msg = f"Attempt {attempt}: {query.validation_error}"
                errors.append(error_msg)
                logger.warning("sql_validation_failed", attempt=attempt, error=query.validation_error)
                continue

            # Try execution if executor provided (use validated/transpiled SQL)
            if db_executor:
                result = await db_executor.execute(query.sql)
                if isinstance(result, QueryError):
                    error_msg = f"Attempt {attempt}: {result.error_message}"
                    errors.append(error_msg)
                    logger.warning("sql_execution_failed", attempt=attempt, error=result.error_message)
                    continue

            logger.info("sql_generation_success", attempt=attempt)
            return query, errors

        # All attempts failed
        final_query = SQLQuery(
            sql=raw_sql if raw_sql else "",
            dialect=self._validator._dialect or "",
            is_valid=False,
            validation_error=f"Failed after {self._max_retries} attempts: {errors[-1] if errors else 'Unknown'}",
            generation_attempt=self._max_retries,
        )
        return final_query, errors


def _clean_sql(raw: str) -> str:
    """Normalize generated SQL into a parser-friendly statement."""
    return sanitize_generated_sql(raw)

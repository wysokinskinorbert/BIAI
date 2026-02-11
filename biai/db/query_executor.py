"""Query executor with timeout and row limiting."""

import time

import pandas as pd

from biai.db.base import DatabaseConnector
from biai.models.query import QueryResult, QueryError
from biai.config.constants import QUERY_TIMEOUT, ROW_LIMIT
from biai.utils.logger import get_logger

logger = get_logger(__name__)


class QueryExecutor:
    """Executes validated SQL queries with safety limits."""

    def __init__(
        self,
        connector: DatabaseConnector,
        timeout: int = QUERY_TIMEOUT,
        row_limit: int = ROW_LIMIT,
    ):
        self._connector = connector
        self._timeout = timeout
        self._row_limit = row_limit

    async def execute(self, sql: str) -> QueryResult | QueryError:
        """Execute a SQL query and return structured result."""
        logger.info("executing_query", sql_preview=sql[:100])
        start = time.time()

        try:
            df = await self._connector.execute_query(sql, timeout=self._timeout)
            elapsed_ms = (time.time() - start) * 1000

            truncated = len(df) > self._row_limit
            if truncated:
                df = df.head(self._row_limit)

            result = QueryResult(
                sql=sql,
                columns=list(df.columns),
                rows=df.values.tolist(),
                row_count=len(df),
                execution_time_ms=round(elapsed_ms, 2),
                truncated=truncated,
            )
            logger.info(
                "query_success",
                rows=result.row_count,
                time_ms=result.execution_time_ms,
                truncated=truncated,
            )
            return result

        except TimeoutError:
            elapsed_ms = (time.time() - start) * 1000
            logger.warning("query_timeout", timeout=self._timeout)
            return QueryError(
                sql=sql,
                error_message=f"Query timed out after {self._timeout}s",
                error_code="TIMEOUT",
            )
        except Exception as e:
            elapsed_ms = (time.time() - start) * 1000
            logger.error("query_error", error=str(e))
            return QueryError(
                sql=sql,
                error_message=str(e),
            )

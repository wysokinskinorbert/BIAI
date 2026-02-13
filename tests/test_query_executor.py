"""Tests for query executor."""

import pytest
import pandas as pd
from unittest.mock import AsyncMock, MagicMock

from biai.db.query_executor import QueryExecutor
from biai.models.query import QueryResult, QueryError


@pytest.fixture
def mock_connector():
    connector = MagicMock()
    connector.execute_query = AsyncMock(
        return_value=pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    )
    return connector


class TestQueryExecutor:
    async def test_execute_success(self, mock_connector):
        executor = QueryExecutor(mock_connector)
        result = await executor.execute("SELECT 1")
        assert isinstance(result, QueryResult)
        assert result.row_count == 3
        assert result.columns == ["a", "b"]

    async def test_execute_timeout(self, mock_connector):
        mock_connector.execute_query = AsyncMock(side_effect=TimeoutError())
        executor = QueryExecutor(mock_connector)
        result = await executor.execute("SELECT 1")
        assert isinstance(result, QueryError)
        assert "timed out" in result.error_message.lower()

    async def test_execute_exception(self, mock_connector):
        mock_connector.execute_query = AsyncMock(side_effect=Exception("DB error"))
        executor = QueryExecutor(mock_connector)
        result = await executor.execute("SELECT 1")
        assert isinstance(result, QueryError)
        assert "DB error" in result.error_message

    async def test_row_limit_truncation(self, mock_connector):
        big_df = pd.DataFrame({"x": range(100)})
        mock_connector.execute_query = AsyncMock(return_value=big_df)
        executor = QueryExecutor(mock_connector, row_limit=10)
        result = await executor.execute("SELECT x")
        assert isinstance(result, QueryResult)
        assert result.row_count == 10
        assert result.truncated is True

"""AI Pipeline - orchestrator for the full question-to-answer flow."""

import json
from typing import AsyncIterator

import httpx
import pandas as pd

from biai.ai.vanna_client import MyVanna, create_vanna_client
from biai.ai.sql_validator import SQLValidator
from biai.ai.self_correction import SelfCorrectionLoop
from biai.ai.chart_advisor import ChartAdvisor
from biai.ai.training import SchemaTrainer
from biai.ai.prompt_templates import DESCRIPTION_PROMPT, SYSTEM_PROMPT, format_dialect_rules
from biai.config.constants import DEFAULT_MODEL
from biai.db.base import DatabaseConnector
from biai.db.dialect import DialectHelper
from biai.db.schema_manager import SchemaManager
from biai.db.query_executor import QueryExecutor
from biai.models.connection import DBType
from biai.models.chart import ChartConfig
from biai.models.query import QueryResult, QueryError, SQLQuery
from biai.utils.logger import get_logger

logger = get_logger(__name__)


class PipelineResult:
    """Complete result from the AI pipeline."""

    def __init__(self):
        self.question: str = ""
        self.sql_query: SQLQuery | None = None
        self.query_result: QueryResult | None = None
        self.query_error: QueryError | None = None
        self.chart_config: ChartConfig | None = None
        self.description: str = ""
        self.errors: list[str] = []
        self.df: pd.DataFrame | None = None

    @property
    def success(self) -> bool:
        return self.query_result is not None and self.sql_query is not None and self.sql_query.is_valid


class AIPipeline:
    """Orchestrates: question → SQL → validate → execute → chart → description."""

    def __init__(
        self,
        connector: DatabaseConnector,
        db_type: DBType = DBType.POSTGRESQL,
        ollama_model: str = DEFAULT_MODEL,
        ollama_host: str = "http://localhost:11434",
        chroma_host: str | None = None,
        chroma_collection: str = "biai_schema",
    ):
        self._connector = connector
        self._db_type = db_type
        self._ollama_host = ollama_host
        self._ollama_model = ollama_model

        # Create Vanna client
        self._vanna = create_vanna_client(
            model=ollama_model,
            ollama_host=ollama_host,
            chroma_host=chroma_host,
            chroma_collection=chroma_collection,
        )

        # Set dialect
        dialect = DialectHelper.get_sqlglot_dialect(db_type)

        # Create components
        self._validator = SQLValidator(dialect=dialect)
        self._correction = SelfCorrectionLoop(self._vanna, self._validator)
        self._chart_advisor = ChartAdvisor(self._vanna)
        self._trainer = SchemaTrainer(self._vanna)
        self._schema_manager = SchemaManager(connector)
        self._query_executor = QueryExecutor(connector)

        # Set system prompt with dialect rules
        rules = DialectHelper.get_rules(db_type)
        self._system_prompt = SYSTEM_PROMPT.format(
            dialect_rules=format_dialect_rules(rules)
        )

        logger.info(
            "pipeline_initialized",
            db_type=db_type.value,
            model=ollama_model,
        )

    @property
    def trainer(self) -> SchemaTrainer:
        return self._trainer

    @property
    def schema_manager(self) -> SchemaManager:
        return self._schema_manager

    async def train_schema(self) -> dict[str, int]:
        """Train Vanna with current database schema."""
        snapshot = await self._schema_manager.get_snapshot()
        examples = DialectHelper.get_examples(self._db_type)
        return self._trainer.train_full(schema=snapshot, examples=examples)

    async def process(self, question: str) -> PipelineResult:
        """Full pipeline: question → SQL → data → chart config."""
        result = PipelineResult()
        result.question = question

        logger.info("pipeline_process", question=question[:80])

        # Step 1: Generate and validate SQL (with self-correction)
        sql_query, errors = await self._correction.generate_with_correction(
            question=question,
            db_executor=self._query_executor,
        )
        result.sql_query = sql_query
        result.errors = errors

        if not sql_query.is_valid:
            logger.warning("pipeline_sql_failed", errors=errors)
            return result

        # Step 2: Execute query
        exec_result = await self._query_executor.execute(sql_query.sql)

        if isinstance(exec_result, QueryError):
            result.query_error = exec_result
            logger.warning("pipeline_query_error", error=exec_result.error_message)
            return result

        result.query_result = exec_result
        result.df = exec_result.to_dataframe()

        # Step 3: Recommend chart
        if result.df is not None and not result.df.empty:
            result.chart_config = self._chart_advisor.recommend(
                question=question,
                sql=sql_query.sql,
                df=result.df,
            )

        logger.info(
            "pipeline_success",
            rows=exec_result.row_count,
            chart_type=result.chart_config.chart_type.value if result.chart_config else "none",
        )
        return result

    async def generate_description(
        self,
        question: str,
        sql: str,
        df: pd.DataFrame,
    ) -> AsyncIterator[str]:
        """Stream a text description of query results."""
        key_points = _extract_key_points(df)

        prompt = DESCRIPTION_PROMPT.format(
            question=question,
            sql=sql,
            row_count=len(df),
            columns=", ".join(df.columns),
            key_points=key_points,
        )

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self._ollama_host}/api/generate",
                    json={
                        "model": self._ollama_model,
                        "prompt": prompt,
                        "stream": True,
                    },
                    timeout=60.0,
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line)
                            if token := data.get("response", ""):
                                yield token
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error("description_generation_failed", error=str(e))
            yield f"Could not generate description: {e}"


def _extract_key_points(df: pd.DataFrame, max_points: int = 5) -> str:
    """Extract key data points for description prompt."""
    if df.empty:
        return "No data"

    points = []
    num_cols = df.select_dtypes(include=["number"]).columns

    for col in num_cols[:3]:
        points.append(f"- {col}: min={df[col].min()}, max={df[col].max()}, avg={df[col].mean():.2f}")

    if len(df) <= max_points:
        points.append(f"- All {len(df)} rows returned")
    else:
        points.append(f"- Top value: {df.iloc[0].to_dict()}")

    return "\n".join(points[:max_points])

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
from biai.ai.process_training import has_process_tables, get_process_documentation, get_process_examples
from biai.ai.process_discovery import ProcessDiscoveryEngine
from biai.ai.process_cache import ProcessDiscoveryCache
from biai.ai.process_training_dynamic import DynamicProcessTrainer

# Module-level singleton: shared across pipeline instances (survives pipeline GC)
_discovery_cache = ProcessDiscoveryCache()
from biai.ai.prompt_templates import DESCRIPTION_PROMPT, SYSTEM_PROMPT, format_dialect_rules
from biai.config.constants import DEFAULT_MODEL, DEFAULT_OLLAMA_HOST, DEFAULT_CHROMA_COLLECTION, USE_DYNAMIC_DISCOVERY
from biai.db.base import DatabaseConnector
from biai.db.dialect import DialectHelper
from biai.db.schema_manager import SchemaManager
from biai.db.query_executor import QueryExecutor
from biai.models.connection import DBType
from biai.models.chart import ChartConfig
from biai.models.process import ProcessFlowConfig
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
        self.process_config: ProcessFlowConfig | None = None
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
        ollama_host: str = DEFAULT_OLLAMA_HOST,
        chroma_host: str | None = None,
        chroma_collection: str = DEFAULT_CHROMA_COLLECTION,
    ):
        self._connector = connector
        self._db_type = db_type
        self._ollama_host = ollama_host
        self._ollama_model = ollama_model

        # Set dialect
        dialect = DialectHelper.get_sqlglot_dialect(db_type)
        dialect_name = DialectHelper.get_dialect_name(db_type)

        # Create Vanna client with correct dialect
        self._vanna = create_vanna_client(
            model=ollama_model,
            ollama_host=ollama_host,
            chroma_host=chroma_host,
            chroma_collection=chroma_collection,
            dialect=dialect_name,
        )

        # Create components
        self._validator = SQLValidator(dialect=dialect)
        self._correction = SelfCorrectionLoop(self._vanna, self._validator)
        self._chart_advisor = ChartAdvisor(self._vanna)
        self._trainer = SchemaTrainer(self._vanna)
        self._schema_manager = SchemaManager(connector)
        self._query_executor = QueryExecutor(connector)

        # Inject dialect rules into Vanna's static documentation
        # This ensures rules are included in every SQL generation prompt
        rules = DialectHelper.get_rules(db_type)
        self._vanna.static_documentation = format_dialect_rules(rules)

        # Dynamic discovery state (cache is module-level singleton)
        self._discovered_processes: list = []

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
        # Reset collections to avoid corrupted HNSW indices from previous sessions
        self._vanna.reset_collections()
        snapshot = await self._schema_manager.get_snapshot()
        # Generate docs and examples from actual schema (real column names)
        docs = DialectHelper.get_documentation(snapshot)
        examples = DialectHelper.get_examples(self._db_type, schema=snapshot)
        is_oracle = self._db_type == DBType.ORACLE

        # Dynamic process discovery (preferred)
        if USE_DYNAMIC_DISCOVERY:
            try:
                # Check module-level cache first
                cached = _discovery_cache.get(self._connector.config)
                if cached is not None:
                    discovered = cached
                else:
                    engine = ProcessDiscoveryEngine(
                        self._connector, snapshot,
                        ollama_host=self._ollama_host,
                        ollama_model=self._ollama_model,
                    )
                    discovered = await engine.discover()
                    _discovery_cache.store(self._connector.config, discovered)

                if discovered:
                    trainer = DynamicProcessTrainer()
                    docs.extend(trainer.generate_documentation(discovered, snapshot))
                    examples.extend(trainer.generate_examples(discovered, is_oracle=is_oracle))
                    self._discovered_processes = discovered
                    logger.info("dynamic_discovery_training_added", count=len(discovered))
            except Exception as e:
                logger.warning("dynamic_discovery_failed", error=str(e))

        # Fallback: add legacy process-specific training data
        if not self._discovered_processes and has_process_tables(snapshot):
            docs.extend(get_process_documentation(snapshot))
            examples.extend(get_process_examples(snapshot, is_oracle=is_oracle))
            logger.info("process_training_data_added", is_oracle=is_oracle)

        return self._trainer.train_full(schema=snapshot, docs=docs, examples=examples)

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

        # Step 3b: Detect process in results
        from biai.ai.process_detector import ProcessDetector
        from biai.ai.process_graph_builder import ProcessGraphBuilder
        from biai.config.constants import PROCESS_DETECTION_ENABLED

        if PROCESS_DETECTION_ENABLED and result.df is not None and not result.df.empty:
            detector = ProcessDetector()
            if detector.detect_in_dataframe(result.df, question):
                builder = ProcessGraphBuilder()
                # Use dynamic discovery if available (check cache if not populated yet)
                discovered_procs = self._discovered_processes
                if not discovered_procs and USE_DYNAMIC_DISCOVERY:
                    cached = _discovery_cache.get(self._connector.config)
                    if cached:
                        discovered_procs = cached
                        self._discovered_processes = cached
                if discovered_procs:
                    process_type, discovered = detector.detect_process_type_dynamic(
                        result.df, sql_query.sql, discovered_procs,
                    )
                else:
                    process_type = detector.detect_process_type(result.df, sql_query.sql)
                    discovered = None
                result.process_config = builder.build(
                    result.df, process_type, question, discovered=discovered,
                )
                if result.process_config:
                    logger.info(
                        "process_detected",
                        process_type=process_type,
                        nodes=len(result.process_config.nodes),
                        edges=len(result.process_config.edges),
                        dynamic=discovered is not None,
                    )

        logger.info(
            "pipeline_success",
            rows=exec_result.row_count,
            chart_type=result.chart_config.chart_type.value if result.chart_config else "none",
            has_process=result.process_config is not None,
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

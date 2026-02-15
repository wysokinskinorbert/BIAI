"""AI Pipeline - orchestrator for the full question-to-answer flow."""

import json
import re
from typing import AsyncIterator

import httpx
import pandas as pd

from biai.ai.vanna_client import MyVanna, create_vanna_client
from biai.ai.sql_validator import SQLValidator
from biai.ai.self_correction import SelfCorrectionLoop
from biai.ai.chart_advisor import ChartAdvisor
from biai.ai.training import SchemaTrainer
from biai.ai.analysis_planner import AnalysisPlanner
from biai.ai.analysis_executor import AnalysisExecutor, StepResult
from biai.ai.process_training import has_process_tables, get_process_documentation, get_process_examples
from biai.ai.process_discovery import ProcessDiscoveryEngine
from biai.ai.process_cache import ProcessDiscoveryCache
from biai.ai.process_training_dynamic import DynamicProcessTrainer

# Module-level singleton: shared across pipeline instances (survives pipeline GC)
_discovery_cache = ProcessDiscoveryCache()
from biai.ai.prompt_templates import DESCRIPTION_PROMPT, SYSTEM_PROMPT, format_dialect_rules
from biai.config.constants import DEFAULT_MODEL, DEFAULT_OLLAMA_HOST, DEFAULT_CHROMA_COLLECTION, USE_DYNAMIC_DISCOVERY, LLM_OPTIONS
from biai.db.base import DatabaseConnector
from biai.db.dialect import DialectHelper, get_categorical_columns, build_distinct_values_docs
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
        self.discovered_process: "DiscoveredProcess | None" = None
        self.description: str = ""
        self.errors: list[str] = []
        self.df: pd.DataFrame | None = None
        self.is_multi_step: bool = False
        self.analysis_steps: list[dict] = []  # [{step, description, status, result_summary, sql}]

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
        schema_name: str = "",
    ):
        self._connector = connector
        self._db_type = db_type
        self._ollama_host = ollama_host
        self._ollama_model = ollama_model
        self._schema_name = schema_name

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
        self._planner = AnalysisPlanner(
            ollama_host=ollama_host, ollama_model=ollama_model,
        )
        self._analysis_executor = AnalysisExecutor(
            self._correction, self._query_executor,
        )

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

    async def discover_context(
        self,
        schemas: list[str] | None = None,
        on_step: object | None = None,
    ) -> "BusinessContext":
        """Progressive context discovery pipeline.

        Steps (with incremental updates via on_step callback):
        1. Schema snapshot → immediate
        2. SchemaGraph build + analysis → ~1-3s
        3. ProcessDiscovery → ~3-8s
        4. Selective profiling (only candidate tables) → parallel
        5. BusinessGlossary (LLM) → ~5-15s

        Args:
            schemas: List of schemas to analyze (None = current schema).
            on_step: Optional async callback(step_name, partial_context).

        Returns:
            BusinessContext with all discovered data.
        """
        import time
        from biai.models.context import BusinessContext
        from biai.ai.metadata_graph import SchemaGraph

        start = time.time()
        ctx = BusinessContext()

        # Step 1: Schema snapshot
        if schemas and len(schemas) > 1:
            snapshot = await self._schema_manager.get_unified_snapshot(schemas)
        else:
            schema = schemas[0] if schemas else self._schema_name
            snapshot = await self._schema_manager.get_snapshot(schema=schema)
        ctx.schema = snapshot
        logger.info("context_step_1_schema", tables=len(snapshot.tables))

        # Step 2: Graph analysis
        graph = SchemaGraph(snapshot)
        stats = graph.get_stats()
        ctx.hub_tables = stats.hub_tables
        ctx.connected_components = stats.connected_components
        ctx.star_schemas = [
            {"fact_table": s.fact_table, "dimensions": s.dimension_tables, "fk_count": s.fk_count}
            for s in stats.star_schemas
        ]
        ctx.bridge_tables = stats.bridge_tables
        ctx.cross_schema_edges = stats.cross_schema_edges
        ctx.table_communities = graph.find_table_communities()
        logger.info(
            "context_step_2_graph",
            hubs=len(ctx.hub_tables),
            components=ctx.connected_components,
            communities=len(set(ctx.table_communities.values())),
        )

        # Step 3: Process discovery
        try:
            cached = _discovery_cache.get(self._connector.config)
            if cached is not None:
                ctx.processes = cached
            else:
                engine = ProcessDiscoveryEngine(
                    self._connector, snapshot,
                    ollama_host=self._ollama_host,
                    ollama_model=self._ollama_model,
                    schema_name=snapshot.schema_name if snapshot.schema_name != "USER" else "",
                )
                ctx.processes = await engine.discover()
                _discovery_cache.store(self._connector.config, ctx.processes)
            logger.info("context_step_3_discovery", processes=len(ctx.processes))
        except Exception as e:
            logger.warning("context_step_3_failed", error=str(e))

        # Step 4: Selective profiling (only candidate process tables)
        try:
            candidate_tables = set()
            for proc in ctx.processes:
                candidate_tables.update(t.upper() for t in proc.tables)
            tables_to_profile = [
                t for t in snapshot.tables
                if t.name.upper() in candidate_tables
            ]
            if tables_to_profile:
                from biai.ai.data_profiler import DataProfiler
                profiler = DataProfiler(self._connector)
                profiles = await profiler.profile_tables_batch(
                    tables_to_profile, concurrency=10, timeout=60.0,
                )
                ctx.profiles = {k: v.model_dump() for k, v in profiles.items()}
                logger.info("context_step_4_profiling", profiled=len(ctx.profiles))
        except Exception as e:
            logger.warning("context_step_4_failed", error=str(e))

        elapsed_ms = int((time.time() - start) * 1000)
        ctx.discovery_duration_ms = elapsed_ms
        ctx.discovered_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        logger.info("context_discovery_complete", duration_ms=elapsed_ms)

        return ctx

    async def train_schema(self) -> dict[str, int]:
        """Train Vanna with current database schema."""
        # Reset collections to avoid corrupted HNSW indices from previous sessions
        self._vanna.reset_collections()
        snapshot = await self._schema_manager.get_snapshot(schema=self._schema_name)
        # Generate docs and examples — auto-select detail level for large schemas
        table_count = len(snapshot.tables)
        if table_count > 200:
            # Large schema: overview only, relevant tables added after discovery
            detail_level = "overview"
            logger.info("train_schema_overview_mode", tables=table_count)
        else:
            detail_level = "full"
        docs = DialectHelper.get_documentation(snapshot, detail_level=detail_level)
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
                        schema_name=snapshot.schema_name if snapshot.schema_name != "USER" else "",
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

        # For large schemas in overview mode: add relevant table details
        if detail_level == "overview" and self._discovered_processes:
            relevant = set()
            for proc in self._discovered_processes:
                relevant.update(proc.tables)
            if relevant:
                relevant_docs = DialectHelper.get_documentation(
                    snapshot, detail_level="relevant",
                    relevant_tables=list(relevant),
                )
                # Replace overview docs with relevant docs (more targeted)
                docs = relevant_docs + docs[len(DialectHelper.get_documentation(snapshot, detail_level="overview")):]
                logger.info("train_schema_relevant_enriched", relevant_tables=len(relevant))

        # Enrich with graph topology context
        try:
            docs.extend(self._build_graph_context_docs(snapshot))
        except Exception as e:
            logger.debug("graph_context_docs_skipped", error=str(e))

        # Fallback: add legacy process-specific training data
        if not self._discovered_processes and has_process_tables(snapshot):
            docs.extend(get_process_documentation(snapshot))
            examples.extend(get_process_examples(snapshot, is_oracle=is_oracle))
            logger.info("process_training_data_added", is_oracle=is_oracle)

        # P3: Auto-discover DISTINCT values for categorical columns
        try:
            cat_cols = get_categorical_columns(snapshot)
            if cat_cols:
                distinct_map = await self._discover_distinct_values(cat_cols)
                value_docs = build_distinct_values_docs(distinct_map)
                docs.extend(value_docs)
                logger.info("distinct_values_discovered", columns=len(cat_cols), docs=len(value_docs))
        except Exception as e:
            logger.warning("distinct_values_discovery_failed", error=str(e))

        return self._trainer.train_full(schema=snapshot, docs=docs, examples=examples)

    def _build_graph_context_docs(self, snapshot) -> list[str]:
        """Build documentation from schema graph topology for LLM context.

        Includes hub tables, star schemas, and cross-schema relationships
        to help LLM understand the database structure for better SQL generation.
        """
        from biai.ai.metadata_graph import SchemaGraph

        graph = SchemaGraph(snapshot)
        stats = graph.get_stats()
        docs: list[str] = []

        # Hub tables (most connected)
        if stats.hub_tables:
            hub_lines = [f"  - {name} ({degree} FK references)" for name, degree in stats.hub_tables[:10]]
            docs.append(
                "DATABASE TOPOLOGY - Hub Tables (most referenced tables, likely central entities):\n"
                + "\n".join(hub_lines)
            )

        # Star schemas
        if stats.star_schemas:
            for ss in stats.star_schemas[:5]:
                dims = ", ".join(ss.dimension_tables[:6])
                docs.append(
                    f"STAR SCHEMA: Fact table '{ss.fact_table}' "
                    f"with dimension tables: {dims}. "
                    f"Use JOINs between {ss.fact_table} and dimensions for analytical queries."
                )

        # Process relationships
        if self._discovered_processes:
            for proc in self._discovered_processes[:10]:
                tables_str = ", ".join(proc.tables[:5])
                stages_str = " -> ".join(proc.stages[:8]) if proc.stages else "unknown stages"
                docs.append(
                    f"BUSINESS PROCESS '{proc.name}': "
                    f"Tables: {tables_str}. "
                    f"Flow: {stages_str}. "
                    f"Confidence: {proc.confidence:.0%}."
                )

        # Cross-schema hints
        if stats.cross_schema_edges > 0:
            cross_edges = graph.get_cross_schema_edges()
            for edge in cross_edges[:5]:
                docs.append(
                    f"CROSS-SCHEMA RELATIONSHIP: {edge.source_table} -> {edge.target_table} "
                    f"(FK: {edge.source_column} references {edge.target_column})"
                )

        if docs:
            logger.info("graph_context_docs_added", count=len(docs))
        return docs

    async def _discover_distinct_values(
        self, columns: list[tuple[str, str]], max_values: int = 30,
    ) -> dict[str, dict[str, list[str]]]:
        """Query DB for DISTINCT values of categorical columns.

        Args:
            columns: List of (table_name, column_name) pairs.
            max_values: Max distinct values per column (skip if more).

        Returns:
            {table_name: {col_name: [val1, val2, ...]}}
        """
        result: dict[str, dict[str, list[str]]] = {}
        for table, col in columns:
            try:
                sql = (
                    f"SELECT DISTINCT {col} FROM {table} "
                    f"WHERE {col} IS NOT NULL "
                    f"ORDER BY {col}"
                )
                df = await self._connector.execute_query(sql, timeout=10)
                values = df.iloc[:, 0].dropna().astype(str).tolist()
                if 0 < len(values) <= max_values:
                    result.setdefault(table, {})[col] = values
            except Exception as e:
                logger.debug("distinct_query_failed", table=table, col=col, error=str(e))
        return result

    async def process(
        self, question: str, context: list[dict] | None = None,
        on_step_update=None,
    ) -> PipelineResult:
        """Full pipeline: question -> SQL -> data -> chart config.

        For complex questions the planner decomposes them into multiple steps,
        each executed independently. Simple questions go through the single-step
        path as before.

        Args:
            on_step_update: Optional async callback(steps: list[dict]) for live
                progress updates from multi-step analysis.
        """
        result = PipelineResult()
        result.question = question

        logger.info("pipeline_process", question=question[:80])

        # Build context-aware question if multi-turn
        effective_question = question
        if context:
            effective_question = self._build_context_question(question, context)

        # Check if multi-step analysis is needed
        try:
            schema_snapshot = await self._schema_manager.get_snapshot(schema=self._schema_name)
        except Exception:
            schema_snapshot = None

        plan = await self._planner.plan(
            question=question,
            schema=schema_snapshot,
            context=None,  # Don't leak conversation context into multi-step planner
        )

        if plan.is_complex and len(plan.steps) > 1:
            return await self._process_multi_step(
                result, question, plan, on_step_update,
            )

        # --- Single-step path (unchanged) ---
        return await self._process_single_step(result, effective_question, question)

    async def _process_single_step(
        self, result: PipelineResult, effective_question: str, original_question: str,
    ) -> PipelineResult:
        """Standard single-query pipeline."""
        # Step 1: Generate and validate SQL (with self-correction)
        sql_query, errors = await self._correction.generate_with_correction(
            question=effective_question,
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

        # Step 3: Recommend chart + detect processes
        self._post_process(result, original_question)

        logger.info(
            "pipeline_success",
            rows=exec_result.row_count,
            chart_type=result.chart_config.chart_type.value if result.chart_config else "none",
            has_process=result.process_config is not None,
        )
        return result

    async def _process_multi_step(
        self,
        result: PipelineResult,
        original_question: str,
        plan,
        on_step_update=None,
    ) -> PipelineResult:
        """Execute multi-step analysis plan."""
        from biai.models.analysis import StepStatus

        result.is_multi_step = True
        logger.info("pipeline_multi_step", steps=len(plan.steps))

        # Build initial step dicts for UI
        result.analysis_steps = [
            {
                "step": str(s.step),
                "description": s.description,
                "status": s.status.value,
                "result_summary": "",
                "sql": "",
            }
            for s in plan.steps
        ]
        if on_step_update:
            await on_step_update(result.analysis_steps)

        async def _step_callback(idx: int, step):
            """Relay per-step progress to PipelineResult and caller."""
            if idx < len(result.analysis_steps):
                result.analysis_steps[idx]["status"] = str(step.status.value)
                result.analysis_steps[idx]["result_summary"] = str(step.result_summary or "")
                result.analysis_steps[idx]["sql"] = str(step.sql or "")
            if on_step_update:
                await on_step_update(result.analysis_steps)

        step_results = await self._analysis_executor.execute(
            plan, on_step_update=_step_callback,
        )

        # Combine results: use the last successful step as the main result
        last_good: StepResult | None = None
        all_dfs: list[pd.DataFrame] = []
        for sr in step_results:
            if sr.success:
                last_good = sr
                all_dfs.append(sr.df)

        if last_good is not None and last_good.df is not None:
            # Prefer concatenated DF if multiple steps produced data
            if len(all_dfs) > 1:
                try:
                    combined = pd.concat(all_dfs, ignore_index=True)
                    result.df = combined
                except Exception:
                    result.df = last_good.df
            else:
                result.df = last_good.df

            result.sql_query = SQLQuery(
                sql=last_good.sql,
                is_valid=True,
            )
            # Build a synthetic QueryResult from the DF
            result.query_result = QueryResult(
                sql=last_good.sql,
                columns=list(result.df.columns),
                rows=[list(row) for _, row in result.df.iterrows()],
                row_count=len(result.df),
            )

            # Post-processing (chart, process detection)
            self._post_process(result, original_question)

            logger.info(
                "pipeline_multi_step_success",
                total_steps=len(plan.steps),
                successful_steps=len(all_dfs),
                rows=len(result.df),
            )
        else:
            # All steps failed
            all_errors = [sr.error for sr in step_results if sr.error]
            result.errors = all_errors or ["All analysis steps failed"]
            result.sql_query = SQLQuery(sql="", is_valid=False)
            logger.warning("pipeline_multi_step_all_failed", errors=all_errors)

        return result

    def _post_process(self, result: PipelineResult, question: str) -> None:
        """Chart recommendation + process detection on a completed result."""
        if result.df is None or result.df.empty:
            return

        # Type coercion: force numeric columns (Decimal/object → numeric)
        for col in result.df.select_dtypes(include=["object"]).columns:
            converted = pd.to_numeric(result.df[col], errors="coerce")
            if converted.notna().any():
                result.df[col] = converted

        # Chart recommendation (wrapped for type safety)
        sql = result.sql_query.sql if result.sql_query else ""
        try:
            result.chart_config = self._chart_advisor.recommend(
                question=question, sql=sql, df=result.df,
            )
        except Exception as e:
            logger.warning("chart_recommendation_failed", error=str(e))
            result.chart_config = None

        # Process detection
        from biai.ai.process_detector import ProcessDetector
        from biai.ai.process_graph_builder import ProcessGraphBuilder
        from biai.config.constants import PROCESS_DETECTION_ENABLED

        if not PROCESS_DETECTION_ENABLED:
            return

        try:
            detector = ProcessDetector()
            if not detector.detect_in_dataframe(result.df, question):
                return

            builder = ProcessGraphBuilder()
            discovered_procs = self._discovered_processes
            if not discovered_procs and USE_DYNAMIC_DISCOVERY:
                cached = _discovery_cache.get(self._connector.config)
                if cached:
                    discovered_procs = cached
                    self._discovered_processes = cached
            if discovered_procs:
                process_type, discovered = detector.detect_process_type_dynamic(
                    result.df, sql, discovered_procs,
                )
            else:
                process_type = detector.detect_process_type(result.df, sql)
                discovered = None
            result.process_config = builder.build(
                result.df, process_type, question, discovered=discovered,
            )
            result.discovered_process = discovered
            if result.process_config:
                logger.info(
                    "process_detected",
                    process_type=process_type,
                    nodes=len(result.process_config.nodes),
                    edges=len(result.process_config.edges),
                    dynamic=discovered is not None,
                )
        except Exception as e:
            logger.warning("process_detection_failed", error=str(e))
            result.process_config = None

    @staticmethod
    def _build_context_question(question: str, context: list[dict]) -> str:
        """Enrich question with conversation context for multi-turn queries."""
        if not context:
            return question
        from biai.ai.prompt_templates import CONTEXT_PROMPT

        ctx_parts = []
        for i, c in enumerate(context[-3:], 1):  # last 3 exchanges
            cols = ", ".join(c.get("columns", [])[:8])
            ctx_parts.append(
                f"Exchange {i}: Q=\"{c['question'][:100]}\" -> "
                f"SQL=\"{c['sql'][:200]}\" -> "
                f"{c['row_count']} rows, columns=[{cols}]"
            )
        ctx_text = "\n".join(ctx_parts)

        enriched = CONTEXT_PROMPT.format(context=ctx_text) + f"\n\nCurrent question: {question}"
        return enriched

    async def generate_description(
        self,
        question: str,
        sql: str,
        df: pd.DataFrame,
    ) -> AsyncIterator[str]:
        """Stream a text description of query results.

        Includes guardrails to prevent SQL-specialized models from
        generating SQL code instead of business descriptions.
        """
        key_points = _extract_key_points(df)

        prompt = DESCRIPTION_PROMPT.format(
            question=question,
            sql=sql,
            row_count=len(df),
            columns=", ".join(df.columns),
            key_points=key_points,
        )

        try:
            tokens: list[str] = []
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self._ollama_host}/api/generate",
                    json={
                        "model": self._ollama_model,
                        "prompt": prompt,
                        "stream": True,
                        "options": {**LLM_OPTIONS, "num_predict": 500},
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
                                tokens.append(token)
                                # Yield cleaned token for streaming
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
    cat_cols = df.select_dtypes(exclude=["number"]).columns

    for col in num_cols[:3]:
        try:
            points.append(f"- {col}: min={df[col].min()}, max={df[col].max()}, avg={df[col].mean():.2f}")
        except (TypeError, ValueError):
            points.append(f"- {col}: {df[col].nunique()} unique values")

    # P5: Explicit ranking for categorical+numeric pairs to prevent LLM ranking errors
    if len(cat_cols) >= 1 and len(num_cols) >= 1:
        cat_col = cat_cols[0]
        val_col = num_cols[0]
        try:
            ranked = df.groupby(cat_col)[val_col].sum().sort_values(ascending=False)
            if len(ranked) >= 2:
                ranking_lines = [f"  #{i+1}: {cat}={val:.2f}" for i, (cat, val) in enumerate(ranked.head(5).items())]
                points.append(f"- RANKING by {val_col} (descending):\n" + "\n".join(ranking_lines))
        except Exception:
            pass

    # Include actual data rows to prevent LLM hallucination
    preview = df.head(max_points).to_string(index=False)
    points.append(f"\nActual data (first {min(len(df), max_points)} rows):\n{preview}")

    return "\n".join(points[:max_points + 2])

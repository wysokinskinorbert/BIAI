"""Chat state with background streaming."""

import asyncio
import re

import reflex as rx

from biai.ai.language import (
    detect_primary_language,
    is_language_compliant,
    normalize_language_enforcement_mode,
    normalize_response_language,
)
from biai.utils.logger import get_logger

logger = get_logger(__name__)

from biai.ai.chart_builder import build_plotly_figure
from biai.ai.echarts_builder import add_chart_annotations, build_echarts_option, can_use_echarts
from biai.models.chart import ChartEngine
from biai.models.message import ChatMessage
from biai.state.database import DBState
from biai.state.query import QueryState
from biai.state.chart import ChartState
from biai.state.process import ProcessState


def _strip_latex(text: str) -> str:
    """Strip LaTeX dollar-sign notation from LLM output."""
    # Remove display math $$...$$
    text = re.sub(r'\$\$(.+?)\$\$', r'\1', text, flags=re.DOTALL)
    # Remove inline math $...$ where content has letters (not currency like $100)
    text = re.sub(r'\$([^$]*[a-zA-Z\\][^$]*)\$', r'\1', text)
    # Remove LaTeX commands: \text{}, \textbf{}, \mathbf{}, etc.
    text = re.sub(r'\\(?:text|textbf|textit|mathbf|mathrm|operatorname)\{([^}]*)\}', r'\1', text)
    # Remove formatting commands
    text = re.sub(r'\\(?:bf|it|rm|cal)\b\s*', '', text)
    # Remove spacing commands \, \; \! \quad \qquad
    text = re.sub(r'\\[,;!]', '', text)
    text = re.sub(r'\\q?quad\b', ' ', text)
    # Remove stray backslashes before letters (e.g. \approx → approx)
    text = re.sub(r'\\([a-zA-Z]+)', r'\1', text)
    return text


def _strip_sql_blocks(text: str) -> str:
    """Strip SQL code blocks and chain-of-thought reasoning from LLM description output."""
    # Remove fenced code blocks (```sql ... ``` or ``` ... ```)
    text = re.sub(r"```(?:sql|SQL)?.*?```", "", text, flags=re.DOTALL)
    # Remove standalone SQL statements that leaked into description
    text = re.sub(
        r"(?m)^\s*(SELECT|WITH)\s+.+?;\s*$", "", text, flags=re.IGNORECASE | re.DOTALL
    )
    # Clean up excessive whitespace left after removal
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _strip_internal_tags(text: str) -> str:
    """Strip internal planner/action tags that may leak from model output."""
    cleaned = re.sub(
        r"<(think|thinking|plan|execute|review|conclusion|analysis|action|result|observation)\b[^>]*>.*?</\1>",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    cleaned = re.sub(
        r"</?(?:plan|execute|review|conclusion|action|result|analysis|think|thinking|observation)\b[^>]*>",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned


def _sanitize_llm_text(text: str) -> str:
    """Sanitize LLM text for safe plain-text chat rendering."""
    cleaned = _strip_internal_tags(_strip_sql_blocks(_strip_latex(text)))
    marker = re.search(
        r"(?:final answer|final summary|ostateczna odpowiedz|finalna odpowiedz)\s*[:\-]",
        cleaned,
        flags=re.IGNORECASE,
    )
    if marker:
        cleaned = cleaned[marker.end():]
    return cleaned.strip()


async def _rewrite_text_language(
    text: str,
    target_language: str,
    ollama_host: str,
    ollama_model: str,
    retry_level: int = 0,
) -> str:
    """Rewrite text into target language to enforce final UI language consistency."""
    cleaned = text.strip()
    if not cleaned:
        return text

    language = normalize_response_language(target_language)
    if language == "en":
        system = "You are an editor. Reply only in English."
        prompt = (
            "Rewrite the text into natural English for a business user.\n"
            "Return only the final answer. No XML/HTML/Markdown tags, no meta commentary.\n"
            "Keep numbers, table names, and meaning unchanged.\n"
            "Do not output Polish words except unavoidable database identifiers.\n\nText:\n"
            f"{cleaned}"
        )
        if retry_level > 0:
            prompt = (
                "STRICT ENFORCEMENT: output must be entirely English.\n"
                "If a phrase cannot be translated, rewrite it into plain English.\n\n"
            ) + prompt
    else:
        system = "Jestes redaktorem. Odpowiadaj tylko po polsku."
        prompt = (
            "Przepisz tekst na naturalny jezyk polski dla uzytkownika biznesowego.\n"
            "Zwroc tylko gotowa odpowiedz: bez planu, bez komentarzy o tlumaczeniu, bez znacznikow XML/HTML/Markdown.\n"
            "Zachowaj liczby, nazwy tabel i znaczenie. Nie dodawaj nowych informacji.\n"
            "Nie uzywaj angielskich zdan poza identyfikatorami SQL.\n\nTekst:\n"
            f"{cleaned}"
        )
        if retry_level > 0:
            prompt = (
                "TRYB SCISLY: odpowiedz ma byc calkowicie po polsku.\n"
                "Jesli nie da sie przetlumaczyc frazy 1:1, sparafrazuj po polsku.\n\n"
            ) + prompt

    try:
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{ollama_host}/api/generate",
                json={
                    "model": ollama_model,
                    "system": system,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0,
                        "seed": 42,
                        "top_k": 1,
                        "num_predict": 700,
                    },
                },
                timeout=45.0,
            )
            resp.raise_for_status()
            rewritten = str(resp.json().get("response", "")).strip()
            if rewritten:
                return rewritten
    except Exception as e:
        logger.warning("language_rewrite_failed", error=str(e))

    return text


def _language_fallback_message(target_language: str) -> str:
    """Fallback text when strict language enforcement cannot be satisfied."""
    language = normalize_response_language(target_language)
    if language == "en":
        return "I could not produce a stable English answer right now. Please try again."
    return "Nie udalo sie przygotowac stabilnej odpowiedzi po polsku. Sprobuj ponownie."


def _make_message(**kwargs) -> dict:
    """Create a validated message dict via ChatMessage model."""
    return ChatMessage(**kwargs).model_dump()


def _generate_suggestions(
    question: str,
    columns: list[str],
    row_count: int,
    language: str = "pl",
) -> list[str]:
    """Generate follow-up query suggestions based on current result."""
    language = language.lower()
    is_en = language == "en"

    def t(pl: str, en: str) -> str:
        return en if is_en else pl

    suggestions = []
    q_lower = question.lower()
    col_names = [c.lower() for c in columns]

    # Time-based drill-down
    time_words = {"month", "year", "daily", "weekly", "trend", "monthly"}
    if any(w in q_lower for w in time_words):
        suggestions.append(t("Pokaż te dane w podziale na kwartały", "Show this data broken down by quarter"))

    # If showing aggregated data, suggest details
    agg_words = {"total", "count", "average", "sum", "avg", "mean"}
    if any(w in q_lower for w in agg_words):
        suggestions.append(
            t(
                "Pokaż 10 najważniejszych pojedynczych rekordów dla tych danych",
                "Show the top 10 individual records for this data",
            )
        )

    # If showing by category, suggest trend
    cat_words = {"by", "per", "wg", "według", "dla", "each"}
    if any(w in q_lower for w in cat_words) and row_count > 1:
        suggestions.append(t("Pokaż trend tych danych w czasie", "Show the trend over time for this data"))

    # If few rows, suggest broader view
    if row_count <= 5:
        suggestions.append(t("Pokaż wszystkie rekordy powiązane z tym zapytaniem", "Show all records related to this query"))
    elif row_count > 20:
        suggestions.append(t("Pokaż tylko 5 najważniejszych wyników", "Show only the top 5 results"))

    # Process-related suggestions
    process_words = {"process", "flow", "etap", "stage", "pipeline", "status"}
    if any(w in q_lower for w in process_words):
        suggestions.append(t("Jakie są wąskie gardła w tym procesie?", "What are the bottlenecks in this process?"))

    return suggestions[:3]


class ChatState(rx.State):
    """Manages chat messages and AI interaction."""

    # Messages: list of dicts created via ChatMessage(...).model_dump()
    messages: list[dict] = []

    # Input
    input_value: str = ""

    # Streaming state
    is_streaming: bool = False
    is_processing: bool = False

    # Cancel streaming
    _cancel_requested: bool = False

    # Schema training flag (lazy: trains on first query, retrains on schema change)
    _schema_trained: bool = False
    _trained_schema: str = ""
    _training_failures: int = 0
    _MAX_TRAINING_RETRIES: int = 2
    _SCHEMA_TRAIN_TIMEOUT_SECONDS: int = 30

    # Clear chat confirmation
    confirm_clear: bool = False

    # Suggested follow-up queries (drill-down)
    suggested_queries: list[str] = []

    # --- Multi-turn conversation context ---
    conversation_context: list[dict] = []  # [{question, sql, columns, row_count}]
    _CONTEXT_LIMIT: int = 5  # keep last N exchanges

    # --- Insight display --- (dict[str, str] for Reflex foreach compatibility)
    insights: list[dict[str, str]] = []

    # --- Multi-step analysis progress ---
    analysis_steps: list[dict[str, str]] = []  # [{step, description, status, result_summary, sql}]
    is_multi_step: bool = False

    # --- Story mode ---
    story_mode: bool = False
    story_data: dict = {
        "context": "",
        "key_findings": [],
        "implications": "",
        "recommendations": [],
        "narrative_type": "general",
        "raw_text": "",
    }

    # --- Story data computed vars (typed for Reflex foreach) ---
    @rx.var
    def story_context(self) -> str:
        return str(self.story_data.get("context", ""))

    @rx.var
    def story_key_findings(self) -> list[str]:
        return [str(f) for f in self.story_data.get("key_findings", [])]

    @rx.var
    def story_implications(self) -> str:
        return str(self.story_data.get("implications", ""))

    @rx.var
    def story_recommendations(self) -> list[str]:
        return [str(r) for r in self.story_data.get("recommendations", [])]

    def set_input(self, value: str):
        self.input_value = value

    def request_clear_chat(self):
        """First click: show confirmation."""
        self.confirm_clear = True

    def cancel_clear_chat(self):
        """Cancel clear chat."""
        self.confirm_clear = False

    def toggle_story_mode(self):
        """Toggle story mode and trigger retroactive generation if data exists."""
        self.story_mode = not self.story_mode
        if self.story_mode:
            # Trigger background story generation for existing data
            return ChatState.generate_story_retroactive

    @rx.event(background=True)
    async def generate_story_retroactive(self):
        """Generate story from existing query data when story mode is toggled ON."""
        # Get last question from conversation context or messages
        question = ""
        async with self:
            if self.conversation_context:
                question = self.conversation_context[-1].get("question", "")
            elif self.messages:
                for msg in reversed(self.messages):
                    if msg.get("role") == "user":
                        question = msg.get("content", "")
                        break

        if not question:
            return

        # Reconstruct DataFrame from QueryState
        import pandas as pd
        columns = []
        rows = []
        async with self:
            query_state = await self.get_state(QueryState)
        async with query_state:
            columns = list(query_state.columns)
            rows = [list(r) for r in query_state.rows]

        if not columns or not rows:
            return

        df = pd.DataFrame(rows, columns=columns)
        # Coerce numeric columns
        for col in df.columns:
            converted = pd.to_numeric(df[col], errors="coerce")
            if converted.notna().any():
                df[col] = converted

        try:
            from biai.ai.storyteller import DataStoryteller
            from biai.state.model import ModelState
            from biai.pages.settings import SettingsState

            async with self:
                model_state = await self.get_state(ModelState)
                settings_state = await self.get_state(SettingsState)

            ollama_host = ""
            selected_nlg_model = ""
            response_language = "pl"
            async with model_state:
                ollama_host = model_state.ollama_host
                selected_nlg_model = model_state.selected_nlg_model
            async with settings_state:
                response_language = settings_state.settings_response_language

            storyteller = DataStoryteller(
                ollama_host=ollama_host,
                ollama_model=selected_nlg_model,
                response_language=response_language,
            )
            # Get insights if available
            insight_objs = None
            async with self:
                insight_dicts = self.insights
            if insight_dicts:
                from biai.models.insight import Insight
                insight_objs = [Insight(**d) for d in insight_dicts]

            story = await storyteller.generate_story(
                question=question, df=df, insights=insight_objs,
            )
            async with self:
                self.story_data = story.model_dump()
        except Exception:
            pass

    def clear_chat(self):
        """Confirmed: clear messages and context."""
        self.messages = []
        self.conversation_context = []
        self.insights = []
        self.analysis_steps = []
        self.is_multi_step = False
        self.confirm_clear = False
        self.suggested_queries = []
        self.story_data = {
            "context": "",
            "key_findings": [],
            "implications": "",
            "recommendations": [],
            "narrative_type": "general",
            "raw_text": "",
        }

    def cancel_streaming(self):
        self._cancel_requested = True

    def run_suggested_query(self, query: str):
        """Set suggested query as input and process it."""
        self.input_value = query
        self.suggested_queries = []
        return ChatState.process_message

    @rx.event(background=True)
    async def process_message(self):
        """Process user message through AI pipeline."""
        question = ""
        async with self:
            self._cancel_requested = False
            question = self.input_value.strip()
            if not question:
                return
            # Add user message
            self.messages.append(
                _make_message(role="user", content=question)
            )
            self.input_value = ""
            self.is_processing = True
            self.is_streaming = True
            self.analysis_steps = []
            self.is_multi_step = False
            self.insights = []
            self.suggested_queries = []

            # Add placeholder AI message
            self.messages.append(
                _make_message(content="Analyzing your question...", is_streaming=True, question=question)
            )

        try:
            # get_state must be called inside async with self (StateProxy requirement)
            async with self:
                db_state = await self.get_state(DBState)

            is_connected = False
            connector = None
            db_type_str = ""
            async with db_state:
                is_connected = db_state.is_connected
                db_type_str = db_state.db_type
                connector = await db_state.get_connector()

            if not is_connected or not connector:
                async with self:
                    self._update_last_message(
                        content="Not connected to database. Please connect first using the sidebar.",
                        is_error=True,
                        is_streaming=False,
                    )
                    self.is_processing = False
                    self.is_streaming = False
                return

            from biai.ai.pipeline import AIPipeline
            from biai.models.connection import DBType
            from biai.state.model import ModelState
            from biai.state.schema import SchemaState
            from biai.pages.settings import SettingsState

            # get_state must be called inside async with self
            async with self:
                model_state = await self.get_state(ModelState)
                schema_state = await self.get_state(SchemaState)
                settings_state = await self.get_state(SettingsState)

            selected_sql_model = ""
            selected_nlg_model = ""
            ollama_host = ""
            async with model_state:
                selected_sql_model = model_state.selected_model
                selected_nlg_model = model_state.selected_nlg_model
                ollama_host = model_state.ollama_host

            selected_schema = ""
            async with schema_state:
                selected_schema = schema_state.selected_schema

            response_language = "pl"
            language_enforcement_mode = "strict"
            async with settings_state:
                response_language = settings_state.settings_response_language
                language_enforcement_mode = normalize_language_enforcement_mode(
                    settings_state.settings_language_enforcement_mode
                )

            pipeline = AIPipeline(
                connector=connector,
                db_type=DBType(db_type_str),
                ollama_model=selected_sql_model,
                ollama_sql_model=selected_sql_model,
                ollama_nlg_model=selected_nlg_model,
                ollama_host=ollama_host,
                schema_name=selected_schema,
                response_language=response_language,
            )

            # Lazy schema training (retrain when schema changes)
            needs_training = False
            async with self:
                if not self._schema_trained or self._trained_schema != selected_schema:
                    needs_training = True
            if needs_training:
                async with self:
                    self._update_last_message(content="Training schema... (first query only)")
                try:
                    await asyncio.wait_for(
                        pipeline.train_schema(),
                        timeout=self._SCHEMA_TRAIN_TIMEOUT_SECONDS,
                    )
                    async with self:
                        self._schema_trained = True
                        self._trained_schema = selected_schema
                        self._training_failures = 0

                    # Propagate discovered processes to ProcessMapState for auto-display
                    try:
                        from biai.ai.pipeline import _discovery_cache as discovery_cache
                        from biai.state.process_map import ProcessMapState, ProcessInfo, EvidenceInfo
                        cached_procs = discovery_cache.get(connector.config)
                        if cached_procs:
                            async with self:
                                pms = await self.get_state(ProcessMapState)
                            async with pms:
                                if not pms.has_processes:
                                    pms.discovered_processes = [
                                        ProcessInfo(
                                            id=p.id,
                                            name=p.name,
                                            description=getattr(p, "description", ""),
                                            stages=[
                                                s.name if hasattr(s, "name") else str(s)
                                                for s in getattr(p, "stages", [])
                                            ],
                                            tables=getattr(p, "tables", []),
                                            confidence=getattr(p, "confidence", 0.0),
                                            evidence=[
                                                EvidenceInfo(
                                                    signal_type=e.signal_type,
                                                    description=e.description,
                                                    strength=e.strength,
                                                )
                                                for e in getattr(p, "evidence", [])
                                            ],
                                        )
                                        for p in cached_procs
                                    ]
                                    pms.show_process_map = True
                    except Exception:
                        pass
                except Exception as e:
                    async with self:
                        self._training_failures += 1
                        if self._training_failures >= self._MAX_TRAINING_RETRIES:
                            # Give up after max retries — mark trained to avoid blocking queries
                            self._schema_trained = True
                            self._trained_schema = selected_schema
                            logger.warning("schema_training_gave_up", attempts=self._training_failures, error=str(e))
                        else:
                            logger.warning("schema_training_failed_retry", attempt=self._training_failures, error=str(e))

            # Build conversation context for multi-turn
            context = []
            async with self:
                context = list(self.conversation_context)

            # Callback for multi-step analysis progress
            async def _on_step_update(steps: list[dict]):
                async with self:
                    self.analysis_steps = steps
                    self.is_multi_step = True
                    self._update_last_message(analysis_steps=steps, is_multi_step=True)

            # Process question (with context)
            result = await pipeline.process(
                question, context=context, on_step_update=_on_step_update,
            )

            # Store multi-step state from result (per-message)
            if result.is_multi_step:
                async with self:
                    self.analysis_steps = result.analysis_steps
                    self.is_multi_step = True
                    self._update_last_message(
                        analysis_steps=result.analysis_steps,
                        is_multi_step=True,
                    )

            if result.success and result.query_result:
                # get_state must be called inside async with self
                async with self:
                    query_state = await self.get_state(QueryState)
                async with query_state:
                    query_state.set_query_result(
                        sql=result.sql_query.sql,
                        columns=result.query_result.columns,
                        rows=result.query_result.rows,
                        row_count=result.query_result.row_count,
                        execution_time_ms=result.query_result.execution_time_ms,
                        truncated=result.query_result.truncated,
                        dialect=result.sql_query.dialect,
                        attempts=result.sql_query.generation_attempt,
                    )

                # Build chart if recommended (wrapped to prevent TypeError crashes)
                async with self:
                    chart_state = await self.get_state(ChartState)
                try:
                    if result.chart_config and result.df is not None:
                        chart_built = False
                        cfg = result.chart_config

                        # Try ECharts for simple chart types
                        if cfg.engine == ChartEngine.ECHARTS and can_use_echarts(cfg.chart_type):
                            echarts_opt = build_echarts_option(cfg, result.df)
                            if echarts_opt:
                                # Auto-annotate bar/line/area charts
                                echarts_opt = add_chart_annotations(echarts_opt, result.df)
                                async with chart_state:
                                    chart_state.set_echarts(echarts_opt, cfg.title, len(result.df))
                                chart_built = True

                        # Fallback to Plotly
                        if not chart_built:
                            plotly_data, plotly_layout = build_plotly_figure(cfg, result.df)
                            if plotly_data:
                                async with chart_state:
                                    chart_state.set_plotly(plotly_data, plotly_layout, cfg.title)
                                chart_built = True

                        # Last resort: heuristic fallback
                        if not chart_built:
                            from biai.ai.chart_advisor import ChartAdvisor
                            fallback = ChartAdvisor()._heuristic_recommend(result.df, question)
                            if can_use_echarts(fallback.chart_type):
                                echarts_opt = build_echarts_option(fallback, result.df)
                                if echarts_opt:
                                    echarts_opt = add_chart_annotations(echarts_opt, result.df)
                                    async with chart_state:
                                        chart_state.set_echarts(echarts_opt, fallback.title, len(result.df))
                                    chart_built = True
                            if not chart_built:
                                plotly_data, plotly_layout = build_plotly_figure(fallback, result.df)
                                if plotly_data:
                                    async with chart_state:
                                        chart_state.set_plotly(plotly_data, plotly_layout, fallback.title)
                                else:
                                    async with chart_state:
                                        chart_state.clear_chart()
                    else:
                        async with chart_state:
                            chart_state.clear_chart()
                except Exception as e:
                    logger.warning("chart_build_failed", error=str(e))
                    async with chart_state:
                        chart_state.clear_chart()

                # Build process flow if detected
                has_process = False
                async with self:
                    process_state = await self.get_state(ProcessState)
                if result.process_config:
                    rf_nodes, rf_edges = result.process_config.to_react_flow_data()
                    # Apply topological sort layout for proper positioning
                    from biai.ai.process_layout import calculate_layout
                    rf_nodes = calculate_layout(rf_nodes, rf_edges, direction="TB")
                    # Find bottleneck node label
                    bottleneck = ""
                    for node in result.process_config.nodes:
                        if node.is_bottleneck:
                            bottleneck = node.label
                            break
                    async with process_state:
                        process_state.set_process_data(
                            nodes=rf_nodes,
                            edges=rf_edges,
                            process_name=result.process_config.title,
                            process_type=result.process_config.process_type,
                            bottleneck=bottleneck,
                            transitions=len(result.process_config.edges),
                            total_instances=result.process_config.total_instances,
                        )
                    has_process = True

                    # Build Sankey from process config edges (always available)
                    try:
                        from biai.ai.echarts_builder import build_sankey_from_process_config
                        sankey = build_sankey_from_process_config(result.process_config)
                        if sankey:
                            async with process_state:
                                process_state.set_sankey_timeline(sankey, {})
                    except Exception as e:
                        logger.debug("sankey_build_skipped", error=str(e))
                else:
                    async with process_state:
                        process_state.clear_process()

                # Stream description
                description_parts = []
                _is_multi = result.is_multi_step
                async for token in pipeline.generate_description(
                    question=question,
                    sql=result.sql_query.sql,
                    df=result.df,
                ):
                    cancel = False
                    async with self:
                        cancel = self._cancel_requested
                    if cancel:
                        break
                    description_parts.append(token)
                    async with self:
                        self._update_last_message(
                            content=_sanitize_llm_text("".join(description_parts)),
                            sql=result.sql_query.sql,
                            has_chart=result.chart_config is not None,
                            has_table=True,
                            has_process=has_process,
                            is_streaming=True,
                            is_multi_step=_is_multi,
                        )

                final_description = _sanitize_llm_text("".join(description_parts))
                if language_enforcement_mode == "strict":
                    candidate = final_description
                    compliant = is_language_compliant(candidate, response_language)
                    for attempt in range(2):
                        if compliant:
                            break
                        candidate = await _rewrite_text_language(
                            candidate,
                            response_language,
                            ollama_host,
                            selected_nlg_model,
                            retry_level=attempt,
                        )
                        candidate = _sanitize_llm_text(candidate)
                        compliant = is_language_compliant(candidate, response_language)
                        logger.info(
                            "language_enforcement_attempt",
                            target=response_language,
                            detected=detect_primary_language(candidate),
                            attempt=attempt + 1,
                            mode=language_enforcement_mode,
                        )

                    if not compliant:
                        logger.warning(
                            "language_enforcement_failed",
                            target=response_language,
                            detected=detect_primary_language(candidate),
                        )
                        candidate = _language_fallback_message(response_language)

                    final_description = candidate
                else:
                    final_description = await _rewrite_text_language(
                        final_description,
                        response_language,
                        ollama_host,
                        selected_nlg_model,
                    )
                    final_description = _sanitize_llm_text(final_description)

                async with self:
                    self._update_last_message(
                        content=final_description,
                        sql=result.sql_query.sql,
                        has_chart=result.chart_config is not None,
                        has_table=True,
                        has_process=has_process,
                        is_streaming=False,
                        is_multi_step=_is_multi,
                    )
                    # Generate drill-down suggestions
                    self.suggested_queries = _generate_suggestions(
                        question,
                        result.query_result.columns,
                        result.query_result.row_count,
                        response_language,
                    )
                    # Store conversation context for multi-turn
                    self.conversation_context.append({
                        "question": question,
                        "sql": result.sql_query.sql,
                        "columns": result.query_result.columns,
                        "row_count": result.query_result.row_count,
                    })
                    # Trim to last N
                    if len(self.conversation_context) > self._CONTEXT_LIMIT:
                        self.conversation_context = self.conversation_context[-self._CONTEXT_LIMIT:]

                # Run insight agent in background (non-blocking)
                if result.df is not None and not result.df.empty:
                    insight_dicts = []
                    try:
                        from biai.ai.insight_agent import InsightAgent
                        agent = InsightAgent()
                        insights = await agent.analyze(result.df, question)
                        insight_dicts = [i.model_dump(mode="json") for i in insights]
                        async with self:
                            self.insights = insight_dicts
                            # Store insights per-message
                            if insight_dicts:
                                self._update_last_message(
                                    insights=insight_dicts,
                                    has_insights=True,
                                )
                        # Update chart annotations with insight data
                        if insight_dicts:
                            async with chart_state:
                                if chart_state.echarts_option:
                                    updated = add_chart_annotations(
                                        chart_state.echarts_option, result.df, insight_dicts
                                    )
                                    chart_state.echarts_option = updated
                    except Exception:
                        pass

                    # Generate data story if story_mode is active
                    story_enabled = False
                    async with self:
                        story_enabled = self.story_mode
                    if story_enabled:
                        try:
                            from biai.ai.storyteller import DataStoryteller
                            storyteller = DataStoryteller(
                                ollama_host=ollama_host,
                                ollama_model=selected_nlg_model,
                                response_language=response_language,
                            )
                            from biai.models.insight import Insight
                            insight_objs = [Insight(**d) for d in insight_dicts] if insight_dicts else []
                            story = await storyteller.generate_story(
                                question=question, df=result.df, insights=insight_objs,
                            )
                            async with self:
                                self.story_data = story.model_dump()
                        except Exception:
                            pass
            else:
                # SQL generation or execution failed
                error_msg = "I couldn't generate a valid query for your question."
                if result.errors:
                    error_msg += f"\n\nErrors:\n" + "\n".join(f"- {e}" for e in result.errors[-2:])
                if result.query_error:
                    error_msg += f"\n\nDatabase error: {result.query_error.error_message}"

                async with self:
                    self._update_last_message(
                        content=error_msg,
                        is_error=True,
                        is_streaming=False,
                    )
                    self.suggested_queries = []

        except Exception as e:
            async with self:
                self._update_last_message(
                    content=f"An error occurred: {str(e)}",
                    is_error=True,
                    is_streaming=False,
                )
                self.suggested_queries = []

        finally:
            async with self:
                self.is_processing = False
                self.is_streaming = False
                self._cancel_requested = False

    def _update_last_message(self, **kwargs):
        """Update the last message in the list."""
        if self.messages:
            msg = self.messages[-1].copy()
            msg.update(kwargs)
            self.messages[-1] = msg

"""Chat state with background streaming."""

import reflex as rx

from biai.state.database import DBState
from biai.state.query import QueryState
from biai.state.chart import ChartState


class ChatState(rx.State):
    """Manages chat messages and AI interaction."""

    # Messages: list of dicts {role, content, sql, has_chart, has_table, is_error, is_streaming}
    messages: list[dict] = []

    # Input
    input_value: str = ""

    # Streaming state
    is_streaming: bool = False
    is_processing: bool = False

    # Error
    last_error: str = ""

    # Schema training flag (lazy: trains on first query)
    _schema_trained: bool = False

    def set_input(self, value: str):
        self.input_value = value

    def clear_chat(self):
        self.messages = []
        self.last_error = ""

    @rx.event(background=True)
    async def process_message(self):
        """Process user message through AI pipeline."""
        question = ""
        async with self:
            question = self.input_value.strip()
            if not question:
                return
            # Add user message
            self.messages.append({
                "role": "user",
                "content": question,
                "sql": None,
                "has_chart": False,
                "has_table": False,
                "is_error": False,
                "is_streaming": False,
            })
            self.input_value = ""
            self.is_processing = True
            self.is_streaming = True

            # Add placeholder AI message
            self.messages.append({
                "role": "assistant",
                "content": "Analyzing your question...",
                "sql": None,
                "has_chart": False,
                "has_table": False,
                "is_error": False,
                "is_streaming": True,
            })

        try:
            # get_state must be called inside async with self (StateProxy requirement)
            async with self:
                db_state = await self.get_state(DBState)

            is_connected = False
            connector = None
            db_type_str = ""
            async with db_state:
                is_connected = db_state.is_connected
                connector = db_state._connector
                db_type_str = db_state.db_type

            if not is_connected or not connector:
                async with self:
                    self._update_last_message(
                        content="Nie jesteś połączony z bazą danych. Użyj panelu Connection w sidebarze aby się połączyć.",
                        is_error=True,
                        is_streaming=False,
                    )
                    self.is_processing = False
                    self.is_streaming = False
                return

            from biai.ai.pipeline import AIPipeline
            from biai.models.connection import DBType
            from biai.components.model_selector import ModelState

            # get_state must be called inside async with self
            async with self:
                model_state = await self.get_state(ModelState)

            selected_model = ""
            ollama_host = ""
            async with model_state:
                selected_model = model_state.selected_model
                ollama_host = model_state.ollama_host

            pipeline = AIPipeline(
                connector=connector,
                db_type=DBType(db_type_str),
                ollama_model=selected_model,
                ollama_host=ollama_host,
            )

            # Lazy schema training (first query only)
            schema_trained = False
            async with self:
                schema_trained = self._schema_trained
            if not schema_trained:
                async with self:
                    self._update_last_message(content="Training schema... (first query only)")
                try:
                    await pipeline.train_schema()
                except Exception:
                    pass  # Training failure is non-fatal
                async with self:
                    self._schema_trained = True

            # Process question
            result = await pipeline.process(question)

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

                # Build chart if recommended
                if result.chart_config and result.df is not None:
                    async with self:
                        chart_state = await self.get_state(ChartState)
                    plotly_data, plotly_layout = _build_plotly_figure(result.chart_config, result.df)
                    if plotly_data:
                        async with chart_state:
                            chart_state.set_plotly(plotly_data, plotly_layout, result.chart_config.title)

                # Stream description
                description_parts = []
                async for token in pipeline.generate_description(
                    question=question,
                    sql=result.sql_query.sql,
                    df=result.df,
                ):
                    description_parts.append(token)
                    async with self:
                        self._update_last_message(
                            content="".join(description_parts),
                            sql=result.sql_query.sql,
                            has_chart=result.chart_config is not None,
                            has_table=True,
                            is_streaming=True,
                        )

                async with self:
                    self._update_last_message(
                        content="".join(description_parts),
                        sql=result.sql_query.sql,
                        has_chart=result.chart_config is not None,
                        has_table=True,
                        is_streaming=False,
                    )
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

        except Exception as e:
            async with self:
                self._update_last_message(
                    content=f"An error occurred: {str(e)}",
                    is_error=True,
                    is_streaming=False,
                )
                self.last_error = str(e)

        finally:
            async with self:
                self.is_processing = False
                self.is_streaming = False

    def _update_last_message(self, **kwargs):
        """Update the last message in the list."""
        if self.messages:
            msg = self.messages[-1].copy()
            msg.update(kwargs)
            self.messages[-1] = msg


def _build_plotly_figure(chart_config, df) -> tuple[list[dict], dict]:
    """Build Plotly figure data from ChartConfig and DataFrame."""
    from biai.models.chart import ChartType

    if chart_config.chart_type == ChartType.TABLE:
        return [], {}

    x_col = chart_config.x_column
    y_cols = chart_config.y_columns

    if not x_col or not y_cols:
        return [], {}

    if x_col not in df.columns:
        return [], {}

    x_data = df[x_col].astype(str).tolist()
    traces: list[dict] = []

    if chart_config.chart_type == ChartType.PIE:
        if y_cols and y_cols[0] in df.columns:
            traces.append({
                "type": "pie",
                "labels": x_data,
                "values": df[y_cols[0]].tolist(),
                "hole": 0.4,
                "textinfo": "label+percent",
            })
    elif chart_config.chart_type == ChartType.SCATTER:
        for y_col in y_cols:
            if y_col in df.columns:
                traces.append({
                    "type": "scatter",
                    "mode": "markers",
                    "x": x_data,
                    "y": df[y_col].tolist(),
                    "name": y_col,
                })
    elif chart_config.chart_type == ChartType.AREA:
        for y_col in y_cols:
            if y_col in df.columns:
                traces.append({
                    "type": "scatter",
                    "mode": "lines",
                    "x": x_data,
                    "y": df[y_col].tolist(),
                    "name": y_col,
                    "fill": "tozeroy",
                })
    elif chart_config.chart_type == ChartType.LINE:
        for y_col in y_cols:
            if y_col in df.columns:
                traces.append({
                    "type": "scatter",
                    "mode": "lines+markers",
                    "x": x_data,
                    "y": df[y_col].tolist(),
                    "name": y_col,
                })
    else:
        # BAR (default)
        for y_col in y_cols:
            if y_col in df.columns:
                traces.append({
                    "type": "bar",
                    "x": x_data,
                    "y": df[y_col].tolist(),
                    "name": y_col,
                })

    layout = {
        "title": {"text": chart_config.title},
        "template": "plotly_dark",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "#e0e0e0"},
        "margin": {"l": 50, "r": 30, "t": 50, "b": 50},
        "showlegend": len(traces) > 1,
    }

    if chart_config.chart_type != ChartType.PIE:
        layout["xaxis"] = {"gridcolor": "#333", "linecolor": "#555"}
        layout["yaxis"] = {"gridcolor": "#333", "linecolor": "#555"}

    return traces, layout

"""Chat state with background streaming."""

import reflex as rx

from biai.state.database import DBState
from biai.state.query import QueryState
from biai.state.chart import ChartState
from biai.state.schema import SchemaState


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
            # Check if in demo mode
            base_state = await self.get_state(rx.State)

            # Check database connection
            db_state = await self.get_state(DBState)

            if not db_state.is_connected or not db_state._connector:
                # Demo mode: generate mock response
                async with self:
                    self._update_last_message(
                        content=_demo_response(question),
                        is_streaming=False,
                    )
                    self.is_processing = False
                    self.is_streaming = False
                return

            # Real mode: use AI pipeline
            from biai.ai.pipeline import AIPipeline
            from biai.models.connection import DBType

            pipeline = AIPipeline(
                connector=db_state._connector,
                db_type=DBType(db_state.db_type),
            )

            # Process question
            result = await pipeline.process(question)

            if result.success and result.query_result:
                # Update QueryState
                query_state = await self.get_state(QueryState)
                async with self:
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
                    chart_state = await self.get_state(ChartState)
                    echarts_opt = _build_echarts_option(result.chart_config, result.df)
                    if echarts_opt:
                        async with self:
                            chart_state.set_echarts(echarts_opt, result.chart_config.title)

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


def _demo_response(question: str) -> str:
    """Generate a demo response when no database is connected."""
    return (
        f"**Demo Mode** - No database connected.\n\n"
        f"Your question: *{question}*\n\n"
        f"Connect to a database (Oracle or PostgreSQL) using the sidebar "
        f"to get real AI-powered answers with charts and data tables."
    )


def _build_echarts_option(chart_config, df) -> dict:
    """Build ECharts option from ChartConfig and DataFrame."""
    from biai.models.chart import ChartType, EChartsOption

    base = EChartsOption.dark_theme_base()

    if chart_config.chart_type == ChartType.TABLE:
        return {}

    x_col = chart_config.x_column
    y_cols = chart_config.y_columns

    if not x_col or not y_cols:
        return {}

    if x_col not in df.columns:
        return {}

    x_data = df[x_col].astype(str).tolist()

    option = {
        **base,
        "title": {"text": chart_config.title, **base.get("title", {})},
        "tooltip": {**base.get("tooltip", {}), "trigger": "axis"},
        "legend": {
            **base.get("legend", {}),
            "data": y_cols,
        },
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
    }

    if chart_config.chart_type == ChartType.PIE:
        # Pie chart
        pie_data = []
        if y_cols and y_cols[0] in df.columns:
            for i, row in df.iterrows():
                pie_data.append({"name": str(row[x_col]), "value": float(row[y_cols[0]])})

        option["series"] = [{
            "type": "pie",
            "radius": ["40%", "70%"],
            "data": pie_data,
            "emphasis": {
                "itemStyle": {
                    "shadowBlur": 10,
                    "shadowOffsetX": 0,
                    "shadowColor": "rgba(0, 0, 0, 0.5)",
                }
            },
        }]
        option.pop("xAxis", None)
        option.pop("yAxis", None)
        option.pop("grid", None)
    else:
        # Axis-based charts (bar, line, scatter, area)
        option["xAxis"] = {
            **base.get("xAxis", {}),
            "type": "category",
            "data": x_data,
        }
        option["yAxis"] = {**base.get("yAxis", {}), "type": "value"}

        series = []
        chart_type_map = {
            ChartType.BAR: "bar",
            ChartType.LINE: "line",
            ChartType.SCATTER: "scatter",
            ChartType.AREA: "line",
        }
        echarts_type = chart_type_map.get(chart_config.chart_type, "bar")

        for y_col in y_cols:
            if y_col in df.columns:
                s = {
                    "name": y_col,
                    "type": echarts_type,
                    "data": df[y_col].tolist(),
                }
                if chart_config.chart_type == ChartType.AREA:
                    s["areaStyle"] = {"opacity": 0.3}
                series.append(s)

        option["series"] = series

    return option

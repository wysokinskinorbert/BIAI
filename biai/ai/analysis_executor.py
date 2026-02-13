"""Multi-step analysis executor — runs planned steps sequentially."""

import pandas as pd

from biai.ai.self_correction import SelfCorrectionLoop
from biai.db.query_executor import QueryExecutor
from biai.models.analysis import AnalysisPlan, AnalysisStep, StepStatus
from biai.models.query import QueryResult, QueryError
from biai.utils.logger import get_logger

logger = get_logger(__name__)


class StepResult:
    """Result of executing one analysis step."""

    def __init__(self, step: AnalysisStep):
        self.step = step
        self.df: pd.DataFrame | None = None
        self.sql: str = ""
        self.error: str = ""

    @property
    def success(self) -> bool:
        return self.df is not None and not self.df.empty


class AnalysisExecutor:
    """Executes multi-step analysis plans."""

    def __init__(
        self,
        correction_loop: SelfCorrectionLoop,
        query_executor: QueryExecutor,
    ):
        self._correction = correction_loop
        self._executor = query_executor

    async def execute(
        self,
        plan: AnalysisPlan,
        on_step_update=None,
    ) -> list[StepResult]:
        """Execute all steps in the plan sequentially.

        Args:
            plan: The analysis plan to execute
            on_step_update: Optional async callback(step_idx, step) for progress
        """
        results: list[StepResult] = []
        step_outputs: dict[int, pd.DataFrame] = {}

        for idx, step in enumerate(plan.steps):
            step.status = StepStatus.RUNNING
            if on_step_update:
                await on_step_update(idx, step)

            result = StepResult(step)

            try:
                # Check dependencies
                for dep in step.depends_on:
                    if dep not in step_outputs:
                        result.error = f"Dependency step {dep} not available"
                        step.status = StepStatus.FAILED
                        break

                if step.status != StepStatus.FAILED:
                    # Generate and execute SQL
                    sql_query, errors = await self._correction.generate_with_correction(
                        question=step.question_for_sql,
                        db_executor=self._executor,
                    )

                    if sql_query.is_valid:
                        exec_result = await self._executor.execute(sql_query.sql)
                        if isinstance(exec_result, QueryResult):
                            result.df = exec_result.to_dataframe()
                            result.sql = sql_query.sql
                            step.sql = sql_query.sql
                            step.row_count = exec_result.row_count
                            step.columns = exec_result.columns
                            step.result_summary = f"{exec_result.row_count} rows, {len(exec_result.columns)} columns"
                            step.status = StepStatus.COMPLETED
                            step_outputs[step.step] = result.df
                        elif isinstance(exec_result, QueryError):
                            result.error = exec_result.error_message
                            step.status = StepStatus.FAILED
                    else:
                        result.error = "; ".join(errors[-2:]) if errors else "SQL generation failed"
                        step.status = StepStatus.FAILED

            except Exception as e:
                result.error = str(e)
                step.status = StepStatus.FAILED
                logger.warning("analysis_step_failed", step=step.step, error=str(e))

            results.append(result)
            if on_step_update:
                await on_step_update(idx, step)

        return results

"""Multi-step analysis models."""

from enum import Enum

from pydantic import BaseModel, Field


class StepType(str, Enum):
    SQL = "sql"
    COMPUTE = "compute"
    COMPARE = "compare"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisStep(BaseModel):
    """Single step in a multi-step analysis."""
    step: int = 1
    type: StepType = StepType.SQL
    description: str = ""
    depends_on: list[int] = Field(default_factory=list)
    question_for_sql: str = ""
    status: StepStatus = StepStatus.PENDING
    result_summary: str = ""
    sql: str = ""
    row_count: int = 0
    columns: list[str] = Field(default_factory=list)


class AnalysisPlan(BaseModel):
    """Plan for multi-step analysis."""
    is_complex: bool = False
    steps: list[AnalysisStep] = Field(default_factory=list)
    final_combination: str = ""

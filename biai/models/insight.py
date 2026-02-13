"""Insight models — autonomous data insights."""

from enum import Enum

from pydantic import BaseModel


class InsightType(str, Enum):
    ANOMALY = "anomaly"
    TREND = "trend"
    CORRELATION = "correlation"
    PARETO = "pareto"
    DISTRIBUTION = "distribution"


class InsightSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Insight(BaseModel):
    """A single data insight."""
    type: InsightType = InsightType.ANOMALY
    title: str = ""
    description: str = ""
    severity: InsightSeverity = InsightSeverity.INFO

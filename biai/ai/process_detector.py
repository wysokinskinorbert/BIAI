"""Detect business processes in SQL query results."""

from __future__ import annotations

import pandas as pd

from biai.utils.logger import get_logger

logger = get_logger(__name__)

# Heuristic patterns for detecting process-related columns
STATUS_COLUMN_PATTERNS = [
    "status", "state", "stage", "step", "phase",
    "from_status", "to_status", "from_state", "to_state",
    "current_step", "current_stage",
]

TIMESTAMP_PATTERNS = [
    "created_at", "updated_at", "changed_at", "entered_at",
    "resolved_at", "completed_at", "started_at",
]

DURATION_PATTERNS = [
    "duration", "elapsed", "time_minutes", "duration_minutes",
    "resolution_minutes",
]

# Keywords in questions suggesting process visualization (Polish + English)
PROCESS_QUESTION_KEYWORDS = [
    "process", "workflow", "flow", "pipeline", "funnel",
    "stages", "steps", "status", "transition", "bottleneck",
    "lifecycle", "journey", "path", "etap", "przeplyw",
    "proces", "lejek", "sciezka", "cykl",
]


class ProcessDetector:
    """Detects process-like data in query results."""

    def is_process_question(self, question: str) -> bool:
        """Check if question implies process visualization."""
        q_lower = question.lower()
        return any(kw in q_lower for kw in PROCESS_QUESTION_KEYWORDS)

    def detect_in_dataframe(self, df: pd.DataFrame, question: str) -> bool:
        """Check if DataFrame contains process-like data."""
        if df.empty or len(df) < 2:
            return False

        cols_lower = [c.lower() for c in df.columns]

        # Heuristic 1: from_status/to_status columns (transition log)
        has_transition = any(
            "from_" in c and ("status" in c or "state" in c)
            for c in cols_lower
        )
        if has_transition:
            logger.debug("process_detected", heuristic="transition_columns")
            return True

        # Heuristic 2: status/stage column + count/avg metric column
        has_status = any(
            any(p in c for p in STATUS_COLUMN_PATTERNS)
            for c in cols_lower
        )
        has_metric = any(
            any(p in c for p in ["count", "avg", "sum", "total", "mean"])
            for c in cols_lower
        )
        if has_status and has_metric:
            logger.debug("process_detected", heuristic="status_plus_metric")
            return True

        # Heuristic 3: question suggests process + data has >= 3 rows
        if self.is_process_question(question) and len(df) >= 3:
            logger.debug("process_detected", heuristic="question_keywords")
            return True

        return False

    def detect_process_type(self, df: pd.DataFrame, sql: str) -> str:
        """Detect which type of process the data represents (legacy heuristic)."""
        sql_upper = sql.upper()
        if "ORDER_PROCESS" in sql_upper or "ORDER_FULFILLMENT" in sql_upper:
            return "order_fulfillment"
        if "PIPELINE" in sql_upper or "SALES_PIPELINE" in sql_upper:
            return "sales_pipeline"
        if "TICKET" in sql_upper or "SUPPORT" in sql_upper:
            return "support_ticket"
        if "APPROVAL" in sql_upper:
            return "approval_workflow"
        return "generic"

    def detect_process_type_dynamic(
        self,
        df: pd.DataFrame,
        sql: str,
        discovered_processes: list,
    ) -> tuple[str, object | None]:
        """Match query to a discovered process.

        Returns (process_name, DiscoveredProcess) or ("generic", None).
        """
        from biai.models.discovery import DiscoveredProcess

        if not discovered_processes:
            return self.detect_process_type(df, sql), None

        sql_upper = sql.upper()
        cols_lower = {c.lower() for c in df.columns}

        best_match: DiscoveredProcess | None = None
        best_score = 0.0

        for proc in discovered_processes:
            if not isinstance(proc, DiscoveredProcess):
                continue
            score = 0.0

            # Match by table name in SQL
            for table in proc.tables:
                if table.upper() in sql_upper:
                    score += 0.5
                    break

            # Match by status column name in DataFrame columns
            if proc.status_column and proc.status_column.column_name.lower() in cols_lower:
                score += 0.3

            # Match by transition columns
            if proc.transition_pattern:
                tp = proc.transition_pattern
                if tp.from_column.lower() in cols_lower and tp.to_column.lower() in cols_lower:
                    score += 0.4

            # Match by stage values in data
            if proc.stages and len(proc.stages) >= 2:
                stage_set = {s.lower() for s in proc.stages}
                for col in df.columns:
                    try:
                        data_values = {str(v).lower() for v in df[col].dropna().unique()}
                        overlap = stage_set & data_values
                        if len(overlap) >= 2:
                            score += 0.3 * (len(overlap) / len(stage_set))
                            break
                    except Exception:
                        continue

            if score > best_score:
                best_score = score
                best_match = proc

        if best_match and best_score >= 0.3:
            logger.info(
                "process_type_dynamic_match",
                process=best_match.id, score=best_score,
            )
            return best_match.id, best_match

        # Fallback to legacy detection
        legacy = self.detect_process_type(df, sql)
        return legacy, None

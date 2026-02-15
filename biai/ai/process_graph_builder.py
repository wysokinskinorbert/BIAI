"""Build React Flow graph from process data."""

from __future__ import annotations

import pandas as pd

from biai.models.discovery import DiscoveredProcess
from biai.models.event_log import EventLog
from biai.models.process import (
    ProcessNode,
    ProcessEdge,
    ProcessFlowConfig,
    ProcessNodeType,
    ProcessEdgeType,
)
from biai.utils.logger import get_logger

logger = get_logger(__name__)


class ProcessGraphBuilder:
    """Builds process flow graph from DataFrame.

    Strategies (in priority order):
    1. Transition columns (from_status, to_status) in the DataFrame
    2. Aggregate columns (stage + count/avg) in the DataFrame
    3. DiscoveredProcess stages (from dynamic discovery)
    """

    def build(
        self,
        df: pd.DataFrame,
        process_type: str,
        question: str,
        discovered: DiscoveredProcess | None = None,
        event_log: EventLog | None = None,
    ) -> ProcessFlowConfig | None:
        """Build process flow from data.

        Strategy priority:
        0. Event log (real transitions from data — highest quality)
        1. Transition columns in DataFrame
        2. Aggregate columns in DataFrame
        3. Discovered process stages
        """
        # Strategy 0: Event log (real transitions confirmed by data)
        if event_log and event_log.events:
            logger.info("process_build_strategy", strategy="event_log")
            return self._build_from_event_log(event_log, question, discovered)

        # Strategy 1: Transition log data (from_status, to_status)
        if self._has_transition_columns(df):
            logger.info("process_build_strategy", strategy="transitions")
            return self._build_from_transitions(df, process_type, question, discovered)

        # Strategy 2: Aggregate data (stage, count)
        if self._has_aggregate_columns(df):
            logger.info("process_build_strategy", strategy="aggregates")
            return self._build_from_aggregates(df, process_type, question, discovered)

        # Strategy 3: Discovered process stages
        if discovered and discovered.stages:
            logger.info("process_build_strategy", strategy="discovery")
            return self._build_from_discovery(df, question, discovered)

        logger.warning("process_build_no_strategy", process_type=process_type)
        return None

    def _build_from_event_log(
        self,
        event_log: EventLog,
        question: str,
        discovered: DiscoveredProcess | None = None,
    ) -> ProcessFlowConfig | None:
        """Build graph from EventLog transition matrix.

        Uses real transition counts as edge weights. Edge thickness is
        proportional to transition frequency. Replaces synthetic edges.
        """
        from biai.ai.dynamic_styler import DynamicStyler

        transition_matrix = event_log.get_transition_matrix()
        if not transition_matrix:
            return None

        # Collect all activities
        activities: set[str] = set()
        for (fr, to), _ in transition_matrix.items():
            activities.add(fr)
            activities.add(to)

        # Order activities using discovered stages if available
        ordered = self._order_states(activities, discovered)

        # Determine start/end nodes
        sources = {fr for fr, _ in transition_matrix.keys()}
        targets = {to for _, to in transition_matrix.keys()}
        start_candidates = sources - targets
        end_candidates = targets - sources

        # Build nodes
        nodes: list[ProcessNode] = []
        max_count = max(transition_matrix.values()) if transition_matrix else 1

        for activity in ordered:
            if activity in start_candidates:
                node_type = ProcessNodeType.START
            elif activity in end_candidates:
                node_type = ProcessNodeType.END
            else:
                node_type = ProcessNodeType.TASK

            label = activity
            if discovered:
                label = discovered.get_label(activity)

            color = DynamicStyler.get_color(activity)
            if discovered:
                custom = discovered.get_stage_color(activity)
                if custom:
                    color = custom

            icon = DynamicStyler.get_icon(activity)
            if discovered:
                custom_icon = discovered.get_stage_icon(activity)
                if custom_icon:
                    icon = custom_icon

            nodes.append(ProcessNode(
                id=activity,
                label=label,
                node_type=node_type,
                color=color,
                icon=icon,
            ))

        # Build edges with weights from transition matrix
        edges: list[ProcessEdge] = []
        for (fr, to), count in transition_matrix.items():
            # Normalize thickness 1-5
            thickness = max(1, min(5, int(count / max_count * 5)))
            edge_type = ProcessEdgeType.ANIMATED if count > max_count * 0.3 else ProcessEdgeType.NORMAL

            edges.append(ProcessEdge(
                id=f"e-{fr}-{to}",
                source=fr,
                target=to,
                label=str(count),
                edge_type=edge_type,
                animated=edge_type == ProcessEdgeType.ANIMATED,
            ))

        if not nodes:
            return None

        return ProcessFlowConfig(
            nodes=nodes,
            edges=edges,
            title=question[:80] if question else event_log.process_id,
        )

    def _has_transition_columns(self, df: pd.DataFrame) -> bool:
        cols = [c.lower() for c in df.columns]
        return any("from_" in c for c in cols) and any("to_" in c for c in cols)

    def _has_aggregate_columns(self, df: pd.DataFrame) -> bool:
        cols = [c.lower() for c in df.columns]
        has_stage = any(
            any(p in c for p in ["status", "stage", "step"])
            for c in cols
        )
        has_count = any(
            any(p in c for p in ["count", "total", "avg", "sum"])
            for c in cols
        )
        return has_stage and has_count

    def _build_from_transitions(
        self,
        df: pd.DataFrame,
        process_type: str,
        question: str,
        discovered: DiscoveredProcess | None = None,
    ) -> ProcessFlowConfig:
        """Build from transition log data (from_status -> to_status + counts)."""
        from_col = next(
            c for c in df.columns
            if "from" in c.lower() and ("status" in c.lower() or "state" in c.lower() or "stage" in c.lower())
        )
        to_col = next(
            c for c in df.columns
            if "to" in c.lower() and ("status" in c.lower() or "state" in c.lower() or "stage" in c.lower())
        )

        count_col = next(
            (c for c in df.columns if "count" in c.lower() or "total" in c.lower()),
            None,
        )
        duration_col = next(
            (c for c in df.columns if "duration" in c.lower() or "avg" in c.lower() or "time" in c.lower()),
            None,
        )

        # Filter out rows with NaN/null from or to status
        df_clean = df.dropna(subset=[from_col, to_col]).copy()
        df_clean = df_clean[
            (df_clean[from_col].astype(str) != "nan")
            & (df_clean[to_col].astype(str) != "nan")
        ]

        # Collect unique states (exclude nan)
        all_states = set(df_clean[from_col].unique()) | set(df_clean[to_col].unique())
        all_states = {str(s) for s in all_states if pd.notna(s) and str(s) != "nan"}

        # Count occurrences per state as source
        state_counts: dict[str, int] = {}
        for _, row in df_clean.iterrows():
            src = str(row[from_col])
            if count_col and pd.notna(row[count_col]):
                state_counts[src] = state_counts.get(src, 0) + int(row[count_col])
            else:
                state_counts[src] = state_counts.get(src, 0) + 1

        # Collect durations per state
        state_durations: dict[str, float] = {}
        if duration_col:
            dur_lists: dict[str, list[float]] = {}
            for _, row in df_clean.iterrows():
                src = str(row[from_col])
                if pd.notna(row[duration_col]):
                    dur_lists.setdefault(src, []).append(float(row[duration_col]))
            state_durations = {k: sum(v) / len(v) for k, v in dur_lists.items()}

        # Determine bottleneck (longest duration)
        bottleneck_state = max(state_durations, key=state_durations.get) if state_durations else None

        # Order states using discovered sequence or data order
        ordered = self._order_states(all_states, discovered)

        # Build nodes
        nodes = []
        for i, state in enumerate(ordered):
            is_first = i == 0
            is_last = i == len(ordered) - 1
            node_type = ProcessNodeType.START if is_first else (
                ProcessNodeType.END if is_last else ProcessNodeType.TASK
            )
            label = discovered.get_label(state) if discovered else state.replace("_", " ").title()
            metadata: dict = {}
            if discovered:
                ai_color = discovered.get_stage_color(state)
                ai_icon = discovered.get_stage_icon(state)
                if ai_color:
                    metadata["ai_color"] = ai_color
                if ai_icon:
                    metadata["ai_icon"] = ai_icon

            nodes.append(ProcessNode(
                id=state,
                label=label,
                node_type=node_type,
                count=state_counts.get(state),
                avg_duration_min=state_durations.get(state),
                is_bottleneck=(state == bottleneck_state),
                metadata=metadata,
            ))

        # Build edges - aggregate by (src, tgt) to ensure unique IDs
        edge_agg: dict[tuple[str, str], int] = {}
        for _, row in df_clean.iterrows():
            src = str(row[from_col])
            tgt = str(row[to_col])
            cnt = int(row[count_col]) if count_col and pd.notna(row[count_col]) else 1
            edge_agg[(src, tgt)] = edge_agg.get((src, tgt), 0) + cnt

        edges = []
        for (src, tgt), cnt in edge_agg.items():
            edges.append(ProcessEdge(
                id=f"{src}->{tgt}",
                source=src,
                target=tgt,
                edge_type=ProcessEdgeType.ANIMATED,
                label=str(cnt),
                count=cnt,
            ))

        total = sum(state_counts.values()) if state_counts else len(df_clean)

        return ProcessFlowConfig(
            nodes=nodes,
            edges=edges,
            title=question.strip().rstrip("?").rstrip(".")[:60],
            process_type=process_type,
            total_instances=total,
        )

    def _build_from_aggregates(
        self,
        df: pd.DataFrame,
        process_type: str,
        question: str,
        discovered: DiscoveredProcess | None = None,
    ) -> ProcessFlowConfig:
        """Build from aggregate data (stage + count/avg)."""
        stage_col = next(
            c for c in df.columns
            if any(p in c.lower() for p in ["status", "stage", "step"])
        )
        count_col = next(
            (c for c in df.columns if "count" in c.lower() or "total" in c.lower()),
            None,
        )
        metric_col = next(
            (c for c in df.columns if "avg" in c.lower() or "duration" in c.lower() or "time" in c.lower()),
            None,
        )

        stages = [str(row[stage_col]) for _, row in df.iterrows()]

        # Determine branch targets to exclude from main sequence
        branch_targets: set[str] = set()
        if discovered and discovered.branches:
            main_stages = set(discovered.stages)
            for _gw, targets in discovered.branches.items():
                for t in targets:
                    if t not in main_stages:
                        branch_targets.add(t)

        ordered = self._order_states(
            set(stages) - branch_targets, discovered,
        )

        # Build nodes
        nodes = []
        bottleneck_val = 0.0
        bottleneck_state = None
        for i, state in enumerate(ordered):
            row_mask = df[stage_col].astype(str) == state
            row = df[row_mask].iloc[0] if row_mask.any() else None

            cnt = int(row[count_col]) if row is not None and count_col and pd.notna(row[count_col]) else None
            dur = float(row[metric_col]) if row is not None and metric_col and pd.notna(row[metric_col]) else None

            if dur is not None and dur > bottleneck_val:
                bottleneck_val = dur
                bottleneck_state = state

            is_first = i == 0
            is_last = i == len(ordered) - 1
            node_type = ProcessNodeType.START if is_first else (
                ProcessNodeType.END if is_last else ProcessNodeType.TASK
            )
            label = discovered.get_label(state) if discovered else state.replace("_", " ").title()
            metadata: dict = {}
            if discovered:
                ai_color = discovered.get_stage_color(state)
                ai_icon = discovered.get_stage_icon(state)
                if ai_color:
                    metadata["ai_color"] = ai_color
                if ai_icon:
                    metadata["ai_icon"] = ai_icon

            nodes.append(ProcessNode(
                id=state,
                label=label,
                node_type=node_type,
                count=cnt,
                avg_duration_min=dur,
                is_bottleneck=(state == bottleneck_state),
                metadata=metadata,
            ))

        # Build sequential edges (suggested — not confirmed by transition data)
        edges = []
        for i in range(len(ordered) - 1):
            src = ordered[i]
            tgt = ordered[i + 1]
            edges.append(ProcessEdge(
                id=f"{src}->{tgt}",
                source=src,
                target=tgt,
                edge_type=ProcessEdgeType.DIMMED,
                label="suggested",
            ))

        # Add branches from discovered process
        if discovered and discovered.branches:
            for gateway, targets in discovered.branches.items():
                if gateway in [n.id for n in nodes]:
                    for tgt in targets:
                        if tgt not in [n.id for n in nodes]:
                            tgt_mask = df[stage_col].astype(str) == tgt
                            tgt_row = df[tgt_mask].iloc[0] if tgt_mask.any() else None
                            tgt_cnt = (
                                int(tgt_row[count_col])
                                if tgt_row is not None and count_col and pd.notna(tgt_row[count_col])
                                else None
                            )
                            tgt_label = discovered.get_label(tgt)
                            tgt_meta: dict = {}
                            ai_color = discovered.get_stage_color(tgt)
                            ai_icon = discovered.get_stage_icon(tgt)
                            if ai_color:
                                tgt_meta["ai_color"] = ai_color
                            if ai_icon:
                                tgt_meta["ai_icon"] = ai_icon
                            nodes.append(ProcessNode(
                                id=tgt,
                                label=tgt_label,
                                node_type=ProcessNodeType.END,
                                count=tgt_cnt,
                                metadata=tgt_meta,
                            ))
                        edge_id = f"{gateway}->{tgt}"
                        if edge_id not in [e.id for e in edges]:
                            edges.append(ProcessEdge(
                                id=edge_id,
                                source=gateway,
                                target=tgt,
                                edge_type=ProcessEdgeType.DIMMED,
                            ))

        return ProcessFlowConfig(
            nodes=nodes,
            edges=edges,
            title=question.strip().rstrip("?").rstrip(".")[:60],
            process_type=process_type,
        )

    def _build_from_discovery(
        self,
        df: pd.DataFrame,
        question: str,
        discovered: DiscoveredProcess,
    ) -> ProcessFlowConfig:
        """Build from discovered process stages when data doesn't match other patterns."""
        stages = discovered.stages
        if not stages:
            return ProcessFlowConfig()

        nodes = []
        for i, state in enumerate(stages):
            is_first = i == 0
            is_last = i == len(stages) - 1
            node_type = ProcessNodeType.START if is_first else (
                ProcessNodeType.END if is_last else ProcessNodeType.TASK
            )
            label = discovered.get_label(state)
            metadata: dict = {}
            ai_color = discovered.get_stage_color(state)
            ai_icon = discovered.get_stage_icon(state)
            if ai_color:
                metadata["ai_color"] = ai_color
            if ai_icon:
                metadata["ai_icon"] = ai_icon

            nodes.append(ProcessNode(
                id=state,
                label=label,
                node_type=node_type,
                count=discovered.stage_counts.get(state),
                metadata=metadata,
            ))

        edges = []
        for i in range(len(stages) - 1):
            edges.append(ProcessEdge(
                id=f"{stages[i]}->{stages[i + 1]}",
                source=stages[i],
                target=stages[i + 1],
                edge_type=ProcessEdgeType.ANIMATED,
            ))

        # Add branches
        for gateway, targets in discovered.branches.items():
            if gateway in [n.id for n in nodes]:
                for tgt in targets:
                    if tgt not in [n.id for n in nodes]:
                        tgt_label = discovered.get_label(tgt)
                        tgt_meta: dict = {}
                        ai_color = discovered.get_stage_color(tgt)
                        ai_icon = discovered.get_stage_icon(tgt)
                        if ai_color:
                            tgt_meta["ai_color"] = ai_color
                        if ai_icon:
                            tgt_meta["ai_icon"] = ai_icon
                        nodes.append(ProcessNode(
                            id=tgt,
                            label=tgt_label,
                            node_type=ProcessNodeType.END,
                            count=discovered.stage_counts.get(tgt),
                            metadata=tgt_meta,
                        ))
                    edge_id = f"{gateway}->{tgt}"
                    if edge_id not in [e.id for e in edges]:
                        edges.append(ProcessEdge(
                            id=edge_id,
                            source=gateway,
                            target=tgt,
                            edge_type=ProcessEdgeType.DIMMED,
                        ))

        return ProcessFlowConfig(
            nodes=nodes,
            edges=edges,
            title=question.strip().rstrip("?").rstrip(".")[:60],
            process_type=discovered.id,
            total_instances=sum(discovered.stage_counts.values()) if discovered.stage_counts else 0,
        )

    def _order_states(
        self,
        states: set[str],
        discovered: DiscoveredProcess | None = None,
    ) -> list[str]:
        """Order states using discovered sequence or lifecycle heuristic.

        Args:
            states: Set of state names found in data.
            discovered: Optional DiscoveredProcess with stage ordering.
        """
        if discovered and discovered.stages:
            known = [str(s) for s in discovered.stages]
            str_states = {str(s) for s in states}
            ordered = [s for s in known if s in str_states]
            remaining = [s for s in str_states if s not in known]
            return ordered + sorted(remaining)
        # Heuristic ordering based on common business process lifecycle patterns
        # Tiebreaker: alphabetical order when scores are equal
        return sorted(
            (str(s) for s in states),
            key=lambda s: (_stage_order_score(s), s.lower()),
        )


# ---------------------------------------------------------------------------
# Heuristic lifecycle ordering for process stages
# ---------------------------------------------------------------------------
# Maps common stage/status names to a position score (0.0 = start, 1.0 = end).
# Stages not in this map get a score of 0.5 (middle).

_STAGE_ORDER_HEURISTIC: dict[str, float] = {
    # === Start / initial stages (0.00 - 0.15) ===
    "new": 0.00, "created": 0.00, "draft": 0.02, "open": 0.05,
    "registered": 0.05, "planned": 0.05, "identified": 0.05,
    "backlog": 0.05, "todo": 0.08,
    "submitted": 0.10, "pending": 0.10, "applied": 0.10,
    "ordered": 0.10, "prescribed": 0.10,
    "scheduled": 0.12, "initiated": 0.12,

    # === Early-middle (0.15 - 0.35) ===
    "screening": 0.18, "phone_screen": 0.20, "preparing": 0.20,
    "proposed": 0.20, "sent": 0.20,
    "sample_collected": 0.22, "confirmed": 0.25, "viewed": 0.25,
    "under_review": 0.25, "assessment": 0.28, "checked_in": 0.28,
    "probation": 0.28, "approved": 0.30,
    "technical_test": 0.32, "interviewing": 0.34, "interview": 0.34,

    # === Middle / active (0.35 - 0.60) ===
    "offer": 0.38, "offer_made": 0.38,
    "active": 0.40, "in_progress": 0.42, "processing": 0.42,
    "shipped": 0.44, "dispensed": 0.45,
    "in_transit": 0.48, "on_hold": 0.50,
    "in_review": 0.50, "review": 0.50, "testing": 0.52,
    "partial_payment": 0.50, "customs": 0.55,
    "on_leave": 0.55,

    # === Late-middle (0.60 - 0.80) ===
    "picked_up": 0.60, "delayed": 0.62,
    "needs_recheck": 0.65, "results_ready": 0.65,
    "overdue": 0.68, "received": 0.70, "reviewed": 0.70,
    "findings_reported": 0.72, "inspected": 0.74,
    "remediation": 0.76, "stored": 0.78,
    "frozen": 0.78, "implemented": 0.80,
    "communicated": 0.80,

    # === Pre-terminal / success (0.80 - 0.92) ===
    "verified": 0.82, "accepted": 0.82, "mitigated": 0.82,
    "passed": 0.84, "reimbursed": 0.86,
    "delivered": 0.88, "paid": 0.88, "filled": 0.88, "hired": 0.88,
    "completed": 0.90, "done": 0.90, "closed": 0.92,
    "resolved": 0.90, "discharged": 0.90, "inactive": 0.90,

    # === Terminal / negative (0.94 - 1.00) ===
    "terminated": 0.94, "rejected": 0.94, "cancelled": 0.94,
    "failed": 0.94, "blocked": 0.94,
    "no_show": 0.96, "written_off": 0.96, "reversed": 0.96,
    "discontinued": 0.96, "damaged": 0.96, "blacklisted": 0.96,
    "deceased": 1.00,
}


def _stage_order_score(stage: str) -> float:
    """Get ordering score for a stage name.

    Tries exact match first, then checks if a known pattern appears inside the
    stage name (e.g., 'order_completed' contains 'completed').
    """
    key = stage.lower().strip()
    if key in _STAGE_ORDER_HEURISTIC:
        return _STAGE_ORDER_HEURISTIC[key]

    # Partial matching: check if known patterns appear inside the stage name
    # Only match patterns of 4+ chars to avoid false positives
    best_score: float | None = None
    best_len = 0
    for pattern, score in _STAGE_ORDER_HEURISTIC.items():
        if len(pattern) >= 4 and pattern in key and len(pattern) > best_len:
            best_score = score
            best_len = len(pattern)

    if best_score is not None:
        return best_score

    return 0.5  # Unknown stages go to the middle

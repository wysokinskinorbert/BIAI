"""Build React Flow graph from process data."""

from __future__ import annotations

import pandas as pd

from biai.models.discovery import DiscoveredProcess
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
    ) -> ProcessFlowConfig | None:
        """Build process flow from data."""
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

        # Build sequential edges
        edges = []
        for i in range(len(ordered) - 1):
            src = ordered[i]
            tgt = ordered[i + 1]
            edges.append(ProcessEdge(
                id=f"{src}->{tgt}",
                source=src,
                target=tgt,
                edge_type=ProcessEdgeType.ANIMATED,
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
        """Order states using discovered sequence or alphabetically.

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
        return sorted(str(s) for s in states)

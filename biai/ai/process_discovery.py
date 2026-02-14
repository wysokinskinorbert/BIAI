"""Dynamic process discovery engine.

Discovers business processes from database schema and data by:
1. Finding status columns (low-cardinality VARCHAR/TEXT with status-like names)
2. Finding transition tables (from_*/to_* column pairs, *_history tables)
3. Analyzing FK chains for entity relationships
4. Querying actual data for stage counts and transitions
5. Optionally using AI (Ollama) to interpret and label processes
"""

import json
import re
from collections import defaultdict

import httpx

from biai.ai.prompt_templates import PROCESS_DISCOVERY_PROMPT
from biai.config.constants import (
    DISCOVERY_MAX_CARDINALITY,
    DISCOVERY_MAX_TABLES,
    DISCOVERY_QUERY_TIMEOUT,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_MODEL,
)
from biai.db.base import DatabaseConnector
from biai.models.discovery import (
    ColumnCandidate,
    DiscoveredProcess,
    EntityChain,
    TransitionPattern,
)
from biai.models.schema import SchemaSnapshot, TableInfo
from biai.utils.logger import get_logger

logger = get_logger(__name__)

# Patterns for status column names
_STATUS_NAME_PATTERNS = [
    r"^status$", r"^state$", r"^stage$", r"^step$", r"^phase$",
    r"^current_st(atus|ep|age)$", r".*_status$", r".*_state$",
    r".*_stage$", r".*_step$", r".*_phase$",
]

# Patterns for transition table column pairs
_TRANSITION_PREFIXES = [
    ("from_", "to_"),
    ("old_", "new_"),
    ("prev_", "next_"),
    ("source_", "target_"),
]

# Table name suffixes suggesting history/audit
_HISTORY_SUFFIXES = ("_history", "_log", "_audit", "_transitions", "_changelog")

# Data types considered "string-like" (status columns)
_STRING_TYPES = {"varchar", "text", "nvarchar", "char", "nchar", "varchar2", "nvarchar2", "clob"}

# Patterns for timestamp columns
_TIMESTAMP_PATTERNS = [
    r".*_at$", r".*_date$", r".*_time$", r".*_timestamp$",
    r"^created$", r"^updated$", r"^changed$",
]

# Patterns for duration columns
_DURATION_PATTERNS = [
    r".*duration.*", r".*elapsed.*", r".*minutes$", r".*hours$",
    r".*time_min.*", r".*resolution_min.*",
]


class ProcessDiscoveryEngine:
    """Discovers business processes from schema and data."""

    def __init__(
        self,
        connector: DatabaseConnector,
        schema: SchemaSnapshot,
        ollama_host: str = DEFAULT_OLLAMA_HOST,
        ollama_model: str = DEFAULT_MODEL,
        schema_name: str = "",
    ):
        self._connector = connector
        self._schema = schema
        self._ollama_host = ollama_host
        self._ollama_model = ollama_model
        self._schema_name = schema_name

    def _qualified_table(self, table_name: str) -> str:
        """Return schema-qualified table name if schema is set."""
        if self._schema_name:
            return f"{self._schema_name}.{table_name}"
        return table_name

    async def discover(self) -> list[DiscoveredProcess]:
        """Run full discovery pipeline and return found processes."""
        tables = self._schema.tables[:DISCOVERY_MAX_TABLES]
        if not tables:
            logger.warning("discovery_no_tables")
            return []

        # Step 1: Find status columns
        status_candidates = self._find_status_columns(tables)
        logger.info("discovery_status_candidates", count=len(status_candidates))

        # Step 2: Find transition tables
        transition_patterns = self._find_transition_tables(tables)
        logger.info("discovery_transition_patterns", count=len(transition_patterns))

        # Step 3: Find FK chains
        entity_chains = self._find_fk_chains(tables)
        logger.info("discovery_entity_chains", count=len(entity_chains))

        # Step 4: Build candidate processes
        candidates = self._build_candidates(
            status_candidates, transition_patterns, entity_chains,
        )

        if not candidates:
            logger.info("discovery_no_candidates")
            return []

        # Step 5: Enrich with actual data
        await self._enrich_with_data(candidates)

        # Step 6: Filter low-confidence
        viable = [c for c in candidates if c.confidence >= 0.3]
        logger.info("discovery_viable", count=len(viable), total=len(candidates))

        # Step 7: Try AI interpretation (best-effort)
        if viable:
            await self._ai_interpret(viable)

        return viable

    # ------------------------------------------------------------------
    # Step 1: Status columns
    # ------------------------------------------------------------------

    def _find_status_columns(self, tables: list[TableInfo]) -> list[ColumnCandidate]:
        """Find columns that look like process statuses."""
        candidates: list[ColumnCandidate] = []
        for table in tables:
            for col in table.columns:
                dtype = col.data_type.lower().split("(")[0].strip()
                if dtype not in _STRING_TYPES:
                    continue
                col_lower = col.name.lower()
                score = 0.0
                for pattern in _STATUS_NAME_PATTERNS:
                    if re.match(pattern, col_lower):
                        score = 0.8 if pattern.startswith("^") and pattern.endswith("$") else 0.5
                        break
                if score > 0:
                    candidates.append(ColumnCandidate(
                        table_name=table.name,
                        column_name=col.name,
                        role="status",
                        confidence=score,
                    ))
        return candidates

    # ------------------------------------------------------------------
    # Step 2: Transition tables
    # ------------------------------------------------------------------

    def _find_transition_tables(self, tables: list[TableInfo]) -> list[TransitionPattern]:
        """Find tables with from/to column pairs (transition logs)."""
        patterns: list[TransitionPattern] = []
        for table in tables:
            col_names = {c.name.lower(): c.name for c in table.columns}

            # Check known prefix pairs
            for from_pfx, to_pfx in _TRANSITION_PREFIXES:
                from_cols = [
                    orig for lower, orig in col_names.items()
                    if lower.startswith(from_pfx)
                ]
                for fc in from_cols:
                    suffix = fc.lower()[len(from_pfx):]
                    to_name = to_pfx + suffix
                    if to_name in col_names:
                        # Find optional count and timestamp columns
                        count_col = self._find_column_by_hint(col_names, ["count", "total", "cnt"])
                        ts_col = self._find_timestamp_column(col_names)
                        patterns.append(TransitionPattern(
                            table_name=table.name,
                            from_column=fc,
                            to_column=col_names[to_name],
                            count_column=count_col,
                            timestamp_column=ts_col,
                        ))

            # Also flag tables with history-like names that have status columns
            if any(table.name.lower().endswith(sfx) for sfx in _HISTORY_SUFFIXES):
                status_cols = [
                    c.name for c in table.columns
                    if any(re.match(p, c.name.lower()) for p in _STATUS_NAME_PATTERNS)
                ]
                if status_cols and not patterns:
                    # Single status column in a history table → implicit self-transition
                    pass  # handled by status_candidates

        return patterns

    # ------------------------------------------------------------------
    # Step 3: FK chains
    # ------------------------------------------------------------------

    def _find_fk_chains(self, tables: list[TableInfo]) -> list[EntityChain]:
        """Discover FK-based entity chains (A -> B -> C)."""
        # Build adjacency: table -> list of (referenced_table, local_col, ref_col)
        adj: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
        table_set = {t.name.upper() for t in tables}

        for table in tables:
            for col in table.columns:
                if col.is_foreign_key and col.foreign_key_ref:
                    ref = col.foreign_key_ref
                    # ref format: "TABLE.COLUMN" or "schema.TABLE.COLUMN"
                    parts = ref.split(".")
                    ref_table = parts[-2] if len(parts) >= 2 else parts[0]
                    if ref_table.upper() in table_set:
                        adj[table.name.upper()].append((
                            ref_table.upper(),
                            col.name,
                            parts[-1] if len(parts) >= 2 else "",
                        ))

        # Find chains of length >= 2 that involve history/log tables
        chains: list[EntityChain] = []
        for table in tables:
            if any(table.name.lower().endswith(sfx) for sfx in _HISTORY_SUFFIXES):
                refs = adj.get(table.name.upper(), [])
                if refs:
                    chain_tables = [table.name]
                    join_keys: list[tuple[str, str]] = []
                    for ref_table, local_col, ref_col in refs:
                        chain_tables.append(ref_table)
                        join_keys.append((local_col, ref_col))
                    entity = table.name.lower()
                    for sfx in _HISTORY_SUFFIXES:
                        entity = entity.removesuffix(sfx)
                    chains.append(EntityChain(
                        tables=chain_tables,
                        join_keys=join_keys,
                        entity_name=entity,
                    ))

        return chains

    # ------------------------------------------------------------------
    # Step 4: Build candidates
    # ------------------------------------------------------------------

    def _build_candidates(
        self,
        status_cols: list[ColumnCandidate],
        transitions: list[TransitionPattern],
        chains: list[EntityChain],
    ) -> list[DiscoveredProcess]:
        """Combine discovery signals into process candidates."""
        candidates: list[DiscoveredProcess] = []
        seen_tables: set[str] = set()

        # Priority 1: Transition patterns (strongest signal)
        for tp in transitions:
            proc_id = tp.table_name.lower().replace(" ", "_")
            if proc_id in seen_tables:
                continue
            seen_tables.add(proc_id)
            candidates.append(DiscoveredProcess(
                id=proc_id,
                name=tp.table_name.replace("_", " ").title(),
                tables=[tp.table_name],
                transition_pattern=tp,
                confidence=0.7,
            ))

        # Priority 2: Status columns (medium signal)
        for sc in status_cols:
            table_key = sc.table_name.lower()
            if table_key in seen_tables:
                # Merge with existing candidate
                for c in candidates:
                    if c.id == table_key:
                        c.status_column = sc
                        c.confidence = min(c.confidence + 0.1, 1.0)
                continue
            seen_tables.add(table_key)
            candidates.append(DiscoveredProcess(
                id=table_key,
                name=sc.table_name.replace("_", " ").title(),
                tables=[sc.table_name],
                status_column=sc,
                confidence=sc.confidence * 0.6,
            ))

        # Enrich with entity chains
        for chain in chains:
            for c in candidates:
                if any(t.upper() in [ct.upper() for ct in chain.tables] for t in c.tables):
                    c.entity_chain = chain
                    c.tables = list(set(c.tables + chain.tables))
                    c.confidence = min(c.confidence + 0.1, 1.0)

        return candidates

    # ------------------------------------------------------------------
    # Step 5: Enrich with data
    # ------------------------------------------------------------------

    async def _enrich_with_data(self, candidates: list[DiscoveredProcess]) -> None:
        """Query DB to get actual stage values and counts."""
        for proc in candidates:
            try:
                if proc.transition_pattern:
                    await self._enrich_transition(proc)
                elif proc.status_column:
                    await self._enrich_status(proc)
            except Exception as e:
                logger.warning(
                    "discovery_enrich_error",
                    process=proc.id, error=str(e),
                )

    async def _enrich_transition(self, proc: DiscoveredProcess) -> None:
        """Get transition data from the database."""
        tp = proc.transition_pattern
        if not tp:
            return
        qualified = self._qualified_table(tp.table_name)
        sql = (
            f"SELECT {tp.from_column}, {tp.to_column}, COUNT(*) AS cnt "
            f"FROM {qualified} "
            f"WHERE {tp.from_column} IS NOT NULL AND {tp.to_column} IS NOT NULL "
            f"GROUP BY {tp.from_column}, {tp.to_column} "
            f"ORDER BY cnt DESC"
        )
        try:
            df = await self._connector.execute_query(sql, timeout=DISCOVERY_QUERY_TIMEOUT)
            if df.empty:
                return

            transitions: list[tuple[str, str, int]] = []
            all_stages: set[str] = set()
            targets: dict[str, set[str]] = defaultdict(set)
            stage_counts: dict[str, int] = defaultdict(int)

            for _, row in df.iterrows():
                fr = str(row.iloc[0])
                to = str(row.iloc[1])
                cnt = int(row.iloc[2])
                transitions.append((fr, to, cnt))
                all_stages.add(fr)
                all_stages.add(to)
                targets[fr].add(to)
                stage_counts[fr] += cnt

            tp.transitions = transitions
            proc.stage_counts = dict(stage_counts)

            # Determine ordering via topological sort
            proc.stages = self._topo_sort(all_stages, transitions)

            # Detect branches (stages with >1 outgoing)
            for src, tgts in targets.items():
                if len(tgts) > 1:
                    proc.branches[src] = sorted(tgts)

            # Boost confidence based on data quality
            if len(proc.stages) >= 3:
                proc.confidence = min(proc.confidence + 0.2, 1.0)

        except Exception as e:
            logger.warning("discovery_transition_query_error", error=str(e))

    async def _enrich_status(self, proc: DiscoveredProcess) -> None:
        """Get status distribution from the database."""
        sc = proc.status_column
        if not sc:
            return
        qualified = self._qualified_table(sc.table_name)
        sql = (
            f"SELECT {sc.column_name}, COUNT(*) AS cnt "
            f"FROM {qualified} "
            f"WHERE {sc.column_name} IS NOT NULL "
            f"GROUP BY {sc.column_name} "
            f"ORDER BY cnt DESC"
        )
        try:
            df = await self._connector.execute_query(sql, timeout=DISCOVERY_QUERY_TIMEOUT)
            if df.empty:
                return

            values: list[str] = []
            counts: dict[str, int] = {}
            for _, row in df.iterrows():
                val = str(row.iloc[0])
                cnt = int(row.iloc[1])
                values.append(val)
                counts[val] = cnt

            sc.distinct_values = values
            sc.cardinality = len(values)

            # Low cardinality is a strong signal
            if sc.cardinality <= DISCOVERY_MAX_CARDINALITY:
                proc.stages = values
                proc.stage_counts = counts
                proc.confidence = min(proc.confidence + 0.15, 1.0)
            else:
                # Too many values - probably not a status column
                proc.confidence *= 0.3

        except Exception as e:
            logger.warning("discovery_status_query_error", error=str(e))

    # ------------------------------------------------------------------
    # Step 6: AI interpretation
    # ------------------------------------------------------------------

    async def _ai_interpret(self, processes: list[DiscoveredProcess]) -> None:
        """Use Ollama to interpret and label discovered processes."""
        # Build schema DDL for context
        ddl_parts = []
        relevant_tables = set()
        for proc in processes:
            relevant_tables.update(t.upper() for t in proc.tables)
        for table in self._schema.tables:
            if table.name.upper() in relevant_tables:
                ddl_parts.append(table.get_ddl())
        schema_ddl = "\n\n".join(ddl_parts) if ddl_parts else "No DDL available."

        # Build candidates JSON
        candidates_data = []
        for proc in processes:
            candidates_data.append({
                "id": proc.id,
                "tables": proc.tables,
                "stages": proc.stages,
                "stage_counts": proc.stage_counts,
                "branches": proc.branches,
                "has_transitions": proc.transition_pattern is not None,
            })

        prompt = PROCESS_DISCOVERY_PROMPT.format(
            schema_ddl=schema_ddl,
            candidates_json=json.dumps(candidates_data, indent=2),
        )

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self._ollama_host}/api/generate",
                    json={
                        "model": self._ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                    },
                    timeout=30.0,
                )
                resp.raise_for_status()
                data = resp.json()
                response_text = data.get("response", "")

            ai_results = json.loads(response_text)
            if not isinstance(ai_results, list):
                ai_results = [ai_results]

            # Apply AI results to processes
            ai_map = {r["id"]: r for r in ai_results if "id" in r}
            for proc in processes:
                ai = ai_map.get(proc.id)
                if not ai:
                    continue
                if "name" in ai:
                    proc.name = ai["name"]
                if "description" in ai:
                    proc.description = ai["description"]
                if "stages" in ai and isinstance(ai["stages"], list):
                    # AI may return numbers instead of strings — coerce all to str
                    proc.stages = [str(s) for s in ai["stages"]]
                if "branches" in ai and isinstance(ai["branches"], dict):
                    proc.branches = {
                        str(k): [str(v) for v in vs]
                        for k, vs in ai["branches"].items()
                        if isinstance(vs, list)
                    }
                if "stage_labels" in ai and isinstance(ai["stage_labels"], dict):
                    proc.ai_labels = {str(k): str(v) for k, v in ai["stage_labels"].items()}
                if "stage_colors" in ai and isinstance(ai["stage_colors"], dict):
                    proc.ai_colors = ai["stage_colors"]
                if "stage_icons" in ai and isinstance(ai["stage_icons"], dict):
                    proc.ai_icons = ai["stage_icons"]

            logger.info("discovery_ai_success", interpreted=len(ai_map))

        except Exception as e:
            logger.warning("discovery_ai_failed", error=str(e))
            # Fallback: generate basic names from table names
            for proc in processes:
                if not proc.description:
                    proc.description = (
                        f"Business process involving {', '.join(proc.tables)}."
                    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _topo_sort(stages: set[str], transitions: list[tuple[str, str, int]]) -> list[str]:
        """Topological sort of stages based on transitions (Kahn's algorithm)."""
        in_degree: dict[str, int] = {s: 0 for s in stages}
        adj: dict[str, list[str]] = defaultdict(list)
        for fr, to, _cnt in transitions:
            if fr in stages and to in stages:
                adj[fr].append(to)
                in_degree[to] = in_degree.get(to, 0) + 1

        queue = sorted([s for s in stages if in_degree.get(s, 0) == 0])
        result: list[str] = []
        while queue:
            node = queue.pop(0)
            result.append(node)
            for neighbor in sorted(adj.get(node, [])):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
            queue.sort()

        # Add any remaining (cycles)
        remaining = [s for s in stages if s not in result]
        result.extend(sorted(remaining))
        return result

    @staticmethod
    def _find_column_by_hint(col_names: dict[str, str], hints: list[str]) -> str | None:
        """Find a column whose name contains any of the hints."""
        for lower, orig in col_names.items():
            for hint in hints:
                if hint in lower:
                    return orig
        return None

    @staticmethod
    def _find_timestamp_column(col_names: dict[str, str]) -> str | None:
        """Find a timestamp-like column."""
        for lower, orig in col_names.items():
            for pattern in _TIMESTAMP_PATTERNS:
                if re.match(pattern, lower):
                    return orig
        return None

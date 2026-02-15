"""Dynamic process discovery engine.

Discovers business processes from database schema and data by:
1. Building SchemaGraph from ALL tables (not limited to first N)
2. Finding status columns (low-cardinality VARCHAR/TEXT with status-like names)
3. Finding transition tables (from_*/to_* column pairs, *_history tables)
4. Analyzing FK chains and graph topology for entity relationships
5. Detecting timestamp sequences (lifecycle columns)
6. Detecting trigger-based process signals
7. Querying actual data for stage counts and transitions
8. Optionally using AI (Ollama) to interpret and label processes

Graph-driven approach: SchemaGraph analyzes structure of ALL tables in-memory (O(n)),
then selective DB queries only for top candidates (max ~20 queries).
"""

import json
import re
from collections import defaultdict

import httpx

from biai.ai.metadata_graph import SchemaGraph
from biai.ai.prompt_templates import PROCESS_DISCOVERY_PROMPT
from biai.config.constants import (
    DISCOVERY_MAX_CARDINALITY,
    DISCOVERY_QUERY_TIMEOUT,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_MODEL,
)
from biai.db.base import DatabaseConnector
from biai.models.discovery import (
    ColumnCandidate,
    DiscoveredProcess,
    EntityChain,
    Evidence,
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
        """Run full discovery pipeline using graph-driven approach.

        Instead of limiting to first N tables, builds a SchemaGraph
        of ALL tables and uses graph topology to find candidates.
        """
        tables = self._schema.tables
        if not tables:
            logger.warning("discovery_no_tables")
            return []

        # Step 1: Build SchemaGraph from ALL tables (fast, in-memory)
        graph = SchemaGraph(self._schema)
        logger.info(
            "discovery_graph_built",
            tables=graph.table_count,
            edges=graph.edge_count,
        )

        # Step 2: Find status columns (scans ALL tables, O(n))
        status_candidates = self._find_status_columns(tables)
        logger.info("discovery_status_candidates", count=len(status_candidates))

        # Step 3: Find transition tables (scans ALL tables, O(n))
        transition_patterns = self._find_transition_tables(tables)
        logger.info("discovery_transition_patterns", count=len(transition_patterns))

        # Step 4: Find FK chains from FULL graph (not limited subset)
        entity_chains = self._find_fk_chains_from_graph(graph)
        logger.info("discovery_entity_chains", count=len(entity_chains))

        # Step 5: Find timestamp sequences (lifecycle columns)
        timestamp_candidates = self._find_timestamp_sequences(tables)
        logger.info("discovery_timestamp_sequences", count=len(timestamp_candidates))

        # Step 6: Find trigger-based process signals
        trigger_signals = self._find_trigger_signals()
        logger.info("discovery_trigger_signals", count=len(trigger_signals))

        # Step 7: Build candidates with evidence from ALL signals + graph topology
        candidates = self._build_candidates(
            status_candidates, transition_patterns, entity_chains,
            graph=graph,
            timestamp_candidates=timestamp_candidates,
            trigger_signals=trigger_signals,
        )

        if not candidates:
            logger.info("discovery_no_candidates")
            return []

        # Step 8: Enrich TOP candidates with actual data (selective DB queries)
        top_candidates = sorted(candidates, key=lambda c: c.confidence, reverse=True)[:20]
        await self._enrich_with_data(top_candidates)

        # Step 9: Filter low-confidence
        viable = [c for c in top_candidates if c.confidence >= 0.3]
        logger.info("discovery_viable", count=len(viable), total=len(candidates))

        # Step 10: Try AI interpretation (best-effort)
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
    # Step 3: FK chains (graph-driven)
    # ------------------------------------------------------------------

    def _find_fk_chains_from_graph(self, graph: SchemaGraph) -> list[EntityChain]:
        """Discover FK chains from SchemaGraph (uses full graph, not limited subset).

        Combines two strategies:
        - Graph FK chains (paths of length 3+ in the FK graph)
        - History/audit table chains (tables with _history suffix + FKs)
        """
        chains: list[EntityChain] = []
        seen_keys: set[str] = set()

        # Strategy 1: Graph-based FK chains
        fk_chains = graph.find_fk_chains(min_length=3)
        for chain_path in fk_chains[:30]:  # top 30 chains
            key = "|".join(chain_path)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            entity_name = chain_path[0].lower().replace("_", " ")
            chains.append(EntityChain(
                tables=list(chain_path),
                entity_name=entity_name,
            ))

        # Strategy 2: History/audit tables with FK refs (original approach)
        for table in self._schema.tables:
            if any(table.name.lower().endswith(sfx) for sfx in _HISTORY_SUFFIXES):
                edges = graph.get_fk_neighbors(table.name)
                if edges:
                    chain_tables = [table.name.upper()]
                    join_keys: list[tuple[str, str]] = []
                    for edge in edges:
                        chain_tables.append(edge.target_table)
                        join_keys.append((edge.source_column, ""))
                    key = "|".join(chain_tables)
                    if key not in seen_keys:
                        seen_keys.add(key)
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
    # Step 5: Timestamp sequences
    # ------------------------------------------------------------------

    def _find_timestamp_sequences(self, tables: list[TableInfo]) -> list[ColumnCandidate]:
        """Find tables with 3+ timestamp columns (lifecycle patterns).

        Tables with columns like created_at, started_at, completed_at
        suggest a process lifecycle.
        """
        candidates: list[ColumnCandidate] = []
        timestamp_types = {"timestamp", "date", "datetime", "timestamptz",
                          "timestamp with time zone", "timestamp without time zone"}

        for table in tables:
            ts_cols = []
            for col in table.columns:
                dtype = col.data_type.lower().split("(")[0].strip()
                col_lower = col.name.lower()
                is_ts_type = dtype in timestamp_types
                is_ts_name = any(re.match(p, col_lower) for p in _TIMESTAMP_PATTERNS)
                if is_ts_type or is_ts_name:
                    ts_cols.append(col.name)

            if len(ts_cols) >= 3:
                candidates.append(ColumnCandidate(
                    table_name=table.name,
                    column_name=", ".join(ts_cols),
                    role="timestamp",
                    distinct_values=ts_cols,
                    cardinality=len(ts_cols),
                    confidence=min(0.3 + len(ts_cols) * 0.1, 0.8),
                ))

        return candidates

    # ------------------------------------------------------------------
    # Step 6: Trigger-based signals
    # ------------------------------------------------------------------

    def _find_trigger_signals(self) -> list[Evidence]:
        """Detect triggers on status/state columns as process signals.

        Triggers on UPDATE of status columns are strong evidence of business processes.
        """
        signals: list[Evidence] = []
        if not self._schema.triggers:
            return signals

        # Build lookup of status column tables
        status_tables: set[str] = set()
        for table in self._schema.tables:
            for col in table.columns:
                col_lower = col.name.lower()
                if any(re.match(p, col_lower) for p in _STATUS_NAME_PATTERNS):
                    status_tables.add(table.name.upper())
                    break

        for trigger in self._schema.triggers:
            trigger_table = trigger.table_name.upper()
            is_update = "UPDATE" in trigger.trigger_event.upper()
            is_status_table = trigger_table in status_tables

            if is_update and is_status_table:
                signals.append(Evidence(
                    signal_type="trigger_on_status",
                    description=(
                        f"Trigger '{trigger.trigger_name}' fires on UPDATE of "
                        f"table '{trigger.table_name}' which has a status column"
                    ),
                    strength=0.8,
                    source_table=trigger.table_name,
                ))
            elif is_update:
                signals.append(Evidence(
                    signal_type="trigger_on_status",
                    description=(
                        f"Trigger '{trigger.trigger_name}' fires on UPDATE of "
                        f"table '{trigger.table_name}'"
                    ),
                    strength=0.4,
                    source_table=trigger.table_name,
                ))

        return signals

    # ------------------------------------------------------------------
    # Step 4: Build candidates
    # ------------------------------------------------------------------

    def _build_candidates(
        self,
        status_cols: list[ColumnCandidate],
        transitions: list[TransitionPattern],
        chains: list[EntityChain],
        *,
        graph: SchemaGraph | None = None,
        timestamp_candidates: list[ColumnCandidate] | None = None,
        trigger_signals: list[Evidence] | None = None,
    ) -> list[DiscoveredProcess]:
        """Combine discovery signals into process candidates with weighted evidence.

        Confidence scoring weights:
            transition_table:   0.30
            status_column:      0.20
            trigger_on_status:  0.15
            fk_hub (degree>5):  0.10
            fk_chain (len>=3):  0.10
            timestamp_sequence: 0.05
            star_schema_fact:   0.05
            data_enrichment:    0.05  (applied later in _enrich_with_data)
        """
        candidates: dict[str, DiscoveredProcess] = {}
        timestamp_candidates = timestamp_candidates or []
        trigger_signals = trigger_signals or []

        # --- Priority 1: Transition patterns (strongest signal, weight=0.30) ---
        for tp in transitions:
            proc_id = tp.table_name.lower().replace(" ", "_")
            proc = candidates.get(proc_id)
            if proc is None:
                proc = DiscoveredProcess(
                    id=proc_id,
                    name=tp.table_name.replace("_", " ").title(),
                    tables=[tp.table_name],
                )
                candidates[proc_id] = proc
            proc.transition_pattern = tp
            proc.evidence.append(Evidence(
                signal_type="transition_table",
                description=f"Table '{tp.table_name}' has from/to columns: "
                            f"{tp.from_column} → {tp.to_column}",
                strength=0.9,
                source_table=tp.table_name,
            ))
            proc.confidence = min(proc.confidence + 0.30, 1.0)

        # --- Priority 2: Status columns (weight=0.20) ---
        for sc in status_cols:
            proc_id = sc.table_name.lower().replace(" ", "_")
            proc = candidates.get(proc_id)
            if proc is None:
                proc = DiscoveredProcess(
                    id=proc_id,
                    name=sc.table_name.replace("_", " ").title(),
                    tables=[sc.table_name],
                )
                candidates[proc_id] = proc
            proc.status_column = sc
            proc.evidence.append(Evidence(
                signal_type="status_column",
                description=f"Column '{sc.column_name}' in table '{sc.table_name}' "
                            f"matches status pattern (confidence={sc.confidence:.1f})",
                strength=sc.confidence,
                source_table=sc.table_name,
                source_column=sc.column_name,
            ))
            proc.confidence = min(proc.confidence + 0.20, 1.0)

        # --- Trigger signals (weight=0.15) ---
        trigger_by_table: dict[str, list[Evidence]] = defaultdict(list)
        for sig in trigger_signals:
            trigger_by_table[sig.source_table.lower().replace(" ", "_")].append(sig)

        for proc_id, sigs in trigger_by_table.items():
            proc = candidates.get(proc_id)
            if proc is None:
                table_name = sigs[0].source_table
                proc = DiscoveredProcess(
                    id=proc_id,
                    name=table_name.replace("_", " ").title(),
                    tables=[table_name],
                )
                candidates[proc_id] = proc
            proc.evidence.extend(sigs)
            proc.confidence = min(proc.confidence + 0.15, 1.0)

        # --- Graph topology signals ---
        if graph:
            # Hub tables (degree > 5, weight=0.10)
            hubs = graph.find_hubs(top_n=30)
            for table_name, degree in hubs:
                if degree < 5:
                    continue
                proc_id = table_name.lower().replace(" ", "_")
                proc = candidates.get(proc_id)
                if proc is None:
                    proc = DiscoveredProcess(
                        id=proc_id,
                        name=table_name.replace("_", " ").title(),
                        tables=[table_name],
                    )
                    candidates[proc_id] = proc
                proc.evidence.append(Evidence(
                    signal_type="hub_table",
                    description=f"Table '{table_name}' is a hub with "
                                f"{degree} FK connections",
                    strength=min(degree / 10.0, 1.0),
                    source_table=table_name,
                ))
                proc.confidence = min(proc.confidence + 0.10, 1.0)

            # Star schema facts (weight=0.05)
            stars = graph.find_star_schemas(min_dimensions=3)
            for star in stars:
                proc_id = star.fact_table.lower().replace(" ", "_")
                proc = candidates.get(proc_id)
                if proc is None:
                    proc = DiscoveredProcess(
                        id=proc_id,
                        name=star.fact_table.replace("_", " ").title(),
                        tables=[star.fact_table] + star.dimension_tables,
                    )
                    candidates[proc_id] = proc
                else:
                    proc.tables = list(set(proc.tables + star.dimension_tables))
                proc.evidence.append(Evidence(
                    signal_type="star_schema_fact",
                    description=f"Table '{star.fact_table}' is a star schema fact "
                                f"with {star.fk_count} dimension FKs",
                    strength=min(star.fk_count / 8.0, 1.0),
                    source_table=star.fact_table,
                ))
                proc.confidence = min(proc.confidence + 0.05, 1.0)

        # --- FK chain enrichment (weight=0.10) ---
        for chain in chains:
            chain_tables_upper = {t.upper() for t in chain.tables}
            matched = False
            for proc in candidates.values():
                proc_tables_upper = {t.upper() for t in proc.tables}
                if proc_tables_upper & chain_tables_upper:
                    proc.entity_chain = chain
                    proc.tables = list(set(proc.tables + chain.tables))
                    proc.evidence.append(Evidence(
                        signal_type="fk_chain",
                        description=f"FK chain of length {len(chain.tables)}: "
                                    f"{' → '.join(chain.tables[:5])}",
                        strength=min(len(chain.tables) / 5.0, 1.0),
                        source_table=chain.tables[0] if chain.tables else "",
                    ))
                    proc.confidence = min(proc.confidence + 0.10, 1.0)
                    matched = True
                    break
            if not matched and len(chain.tables) >= 3:
                proc_id = chain.entity_name or chain.tables[0].lower()
                proc_id = proc_id.replace(" ", "_")
                if proc_id not in candidates:
                    proc = DiscoveredProcess(
                        id=proc_id,
                        name=chain.entity_name.replace("_", " ").title()
                             if chain.entity_name else chain.tables[0],
                        tables=list(chain.tables),
                        entity_chain=chain,
                    )
                    proc.evidence.append(Evidence(
                        signal_type="fk_chain",
                        description=f"FK chain of length {len(chain.tables)}: "
                                    f"{' → '.join(chain.tables[:5])}",
                        strength=min(len(chain.tables) / 5.0, 1.0),
                        source_table=chain.tables[0] if chain.tables else "",
                    ))
                    proc.confidence = 0.10
                    candidates[proc_id] = proc

        # --- Timestamp sequences (weight=0.05) ---
        for ts_cand in timestamp_candidates:
            proc_id = ts_cand.table_name.lower().replace(" ", "_")
            proc = candidates.get(proc_id)
            if proc is None:
                proc = DiscoveredProcess(
                    id=proc_id,
                    name=ts_cand.table_name.replace("_", " ").title(),
                    tables=[ts_cand.table_name],
                )
                candidates[proc_id] = proc
            proc.evidence.append(Evidence(
                signal_type="timestamp_sequence",
                description=f"Table '{ts_cand.table_name}' has {ts_cand.cardinality} "
                            f"timestamp columns: {ts_cand.column_name}",
                strength=ts_cand.confidence,
                source_table=ts_cand.table_name,
            ))
            proc.confidence = min(proc.confidence + 0.05, 1.0)

        # Filter: require at least 2 evidence signals for standalone candidates
        result = []
        for proc in candidates.values():
            if len(proc.evidence) >= 2 or proc.confidence >= 0.25:
                result.append(proc)

        return result

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

            # Boost confidence based on data quality (data_enrichment weight=0.05)
            if len(proc.stages) >= 3:
                proc.evidence.append(Evidence(
                    signal_type="data_enrichment",
                    description=f"Transition data has {len(proc.stages)} distinct "
                                f"stages with {len(transitions)} transitions",
                    strength=min(len(proc.stages) / 8.0, 1.0),
                    source_table=tp.table_name,
                ))
                proc.confidence = min(proc.confidence + 0.05, 1.0)

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

            # Low cardinality is a strong signal (data_enrichment weight=0.05)
            if sc.cardinality <= DISCOVERY_MAX_CARDINALITY:
                proc.stages = values
                proc.stage_counts = counts
                proc.evidence.append(Evidence(
                    signal_type="data_enrichment",
                    description=f"Status column '{sc.column_name}' has "
                                f"{sc.cardinality} distinct values",
                    strength=min(1.0 - sc.cardinality / DISCOVERY_MAX_CARDINALITY, 1.0),
                    source_table=sc.table_name,
                    source_column=sc.column_name,
                ))
                proc.confidence = min(proc.confidence + 0.05, 1.0)
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

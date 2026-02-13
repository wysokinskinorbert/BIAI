# BIAI - Architektura Modulu Wizualizacji Procesow Biznesowych

**Data:** 2026-02-13
**Autor:** arch-designer (Claude Opus 4.6)
**Bazuje na:** poc.md, architecture.md, analysis_poc_gaps.md, analysis_codebase_map.md, analysis_viz_technologies.md, analysis_test_data.md

> **UWAGA:** Implementacja odeszla od niektorych elementow tego planu. Patrz sekcja "Zmiany Architekturalne vs Plan" na koncu dokumentu.

---

## 1. Streszczenie

Dokument definiuje kompletna architekture modulu wizualizacji procesow biznesowych dla aplikacji BIAI. Modul wprowadza:

1. **Agent Router** - klasyfikacja pytan uzytkownika (SQL vs diagram procesu)
2. **Process Detector** - automatyczne wykrywanie tabel procesowych w schemacie DB
3. **Process Data Transformer** - konwersja wynikow SQL na format React Flow (nodes/edges)
4. **React Flow Component** - interaktywna wizualizacja z animacjami, dark theme, glow effects
5. **State Management** - nowy `ProcessState` zintegrowany z istniejacym pipeline

**Strategia:** Minimalna ingerencja w istniejacy kod (~3150 LOC). Nowe moduly + punktowe modyfikacje w 5 istniejacych plikach.

**Kluczowa zasada:** Process Pipeline jest ROZSZERZENIEM istniejacego SQL Pipeline, nie osobna sciezka. Najpierw generuje SQL i pobiera dane, potem analizuje wyniki pod katem danych procesowych i buduje React Flow graf.

---

## 2. Decyzje Architektoniczne

| Decyzja | Wybor | Uzasadnienie |
|---------|-------|-------------|
| Glowna technologia wizualizacji | **React Flow (@xyflow/react v12.9.0)** | Oficjalny przyklad integracji w dokumentacji Reflex, Turbo Flow (glow+dark), animowane krawedzie, custom nodes, MIT License, 27k+ stars |
| Uzupelniajaca technologia | **Mermaid.js** (opcjonalna, Faza 2) | Proste statyczne diagramy, tekstowa definicja DSL |
| Layout engine | **Server-side topological sort** (Dagre-like) | Brak dodatkowej JS dependency, wystarczajacy dla procesow (max ~20 stanow) |
| Agent routing | **2-stopniowy: keyword heuristic + LLM fallback** | Szybki, deterministyczny, z LLM safety net |
| Styl wizualny | **Turbo Flow** (glow, gradients, dark theme) | Zgodny z POC wymaganiami |
| Integracja | **Rozszerzenie istniejacego pipeline** | Re-uzywa cala warstwe AI+DB, minimalizuje ingerencje |

---

## 3. Rozszerzony Data Flow

### 3.1 Aktualny flow (bez zmian)

```
User Question -> ChatState.process_message()
  -> AIPipeline.process(question)
    -> SelfCorrectionLoop.generate_with_correction()
      -> Vanna.generate_sql() + SQLValidator.validate()
    -> QueryExecutor.execute(sql)
    -> ChartAdvisor.recommend(df)
  -> QueryState.set_query_result()
  -> ChartState.set_plotly()
  -> stream generate_description()
```

### 3.2 Nowy flow (rozszerzony)

```
User Question -> ChatState.process_message()
  |
  [NOWY] AgentRouter.classify(question, process_tables)
  |
  +--- SQL_QUERY ---> [bez zmian] AIPipeline.process(question)
  |
  +--- PROCESS_DIAGRAM ---> [NOWY] Process Pipeline:
  |     1. ProcessDetector.detect(schema) -> ProcessDefinition
  |     2. Generuj process SQL (PROCESS_SQL_PROMPT)
  |     3. QueryExecutor.execute(process_sql)
  |     4. ProcessTransformer.transform(df, process_def) -> ReactFlowData
  |     5. calculate_layout(nodes, edges) -> positioned nodes
  |     6. ProcessState.set_process_data(nodes, edges, metrics)
  |     7. Dashboard renderuje process_flow_card()
  |
  +--- HYBRID ---> [NOWY] Oba pipeline'y:
        1. AIPipeline.process(question) -> chart + table (jak wczesniej)
        2. Process Pipeline -> process flow (dodatkowy)
```

---

## 4. Agent Router (AI Decision Layer)

### 4.1 Cel

Klasyfikacja pytania uzytkownika do jednej z trzech kategorii:

| Kategoria | Opis | Przyklad |
|-----------|------|----------|
| `SQL_QUERY` | Standardowe zapytanie danych | "Ile zamowien bylo w styczniu?" |
| `PROCESS_DIAGRAM` | Wizualizacja procesu biznesowego | "Pokaz proces realizacji zamowien" |
| `HYBRID` | Dane + wizualizacja procesu | "Pokaz bottleneck w procesie zamowien" |

### 4.2 Plik: `biai/ai/agent_router.py` (~120 LOC)

```python
"""Agent Router - classifies user questions into processing paths."""

import re
from enum import Enum

from biai.utils.logger import get_logger

logger = get_logger(__name__)


class QueryIntent(str, Enum):
    """Classification of user question intent."""
    SQL_QUERY = "sql_query"
    PROCESS_DIAGRAM = "process_diagram"
    HYBRID = "hybrid"


class AgentRouter:
    """Routes user questions to appropriate processing pipeline."""

    # Strong process signals (always -> PROCESS_DIAGRAM)
    STRONG_PROCESS_PATTERNS: list[str] = [
        "pokaz proces", "show process", "diagram", "wizualizuj",
        "visualize", "przebieg procesu", "process flow",
        "flow chart", "schemat procesu", "etapy procesu",
        "pokaz flow", "pokaz przeplyw",
    ]

    # Keywords indicating process visualization request
    PROCESS_KEYWORDS: list[str] = [
        "proces", "przebieg", "przeplyw", "workflow", "etapy", "kroki",
        "diagram", "wizualizacja procesu", "schemat procesu", "flow",
        "sciezka", "cykl zycia", "lifecycle", "pipeline", "lejek",
        "funnel", "bottleneck", "waskie gardlo",
        "process", "stages", "steps", "path",
    ]

    # Keywords indicating data/SQL query
    SQL_KEYWORDS: list[str] = [
        "ile", "jaki", "jaka", "jakie", "policz", "suma", "sredni",
        "srednia", "maximum", "minimum", "top", "ranking",
        "how many", "what", "count", "sum", "average", "total",
        "list", "show data", "compare", "trend",
    ]

    def __init__(self, vanna_client=None):
        self._vanna = vanna_client

    def classify(
        self, question: str, process_tables: list[str] | None = None
    ) -> QueryIntent:
        """Classify question intent using heuristics + optional LLM fallback.

        Args:
            question: User's question
            process_tables: List of detected process table names from schema

        Returns:
            QueryIntent classification
        """
        intent = self._heuristic_classify(question, process_tables)

        # If heuristic is uncertain and LLM available, use LLM
        if intent is None and self._vanna:
            intent = self._llm_classify(question)

        return intent or QueryIntent.SQL_QUERY

    def _heuristic_classify(
        self, question: str, process_tables: list[str] | None = None
    ) -> QueryIntent | None:
        """Heuristic-based classification."""
        q_lower = question.lower()

        # Count keyword matches
        process_score = sum(1 for kw in self.PROCESS_KEYWORDS if kw in q_lower)
        sql_score = sum(1 for kw in self.SQL_KEYWORDS if kw in q_lower)

        # Boost process score if question mentions known process tables
        if process_tables:
            for table in process_tables:
                table_words = table.lower().replace("_", " ")
                if table_words in q_lower or table.lower() in q_lower:
                    process_score += 2

        # Strong process signals
        strong_process = any(
            phrase in q_lower for phrase in self.STRONG_PROCESS_PATTERNS
        )

        if strong_process:
            if sql_score >= 2:
                return QueryIntent.HYBRID
            return QueryIntent.PROCESS_DIAGRAM

        # Ambiguous - let LLM decide
        if process_score > 0 and sql_score > 0:
            return None

        if process_score >= 2:
            return QueryIntent.PROCESS_DIAGRAM

        if sql_score >= 1:
            return QueryIntent.SQL_QUERY

        return None  # default to SQL_QUERY in classify()

    def _llm_classify(self, question: str) -> QueryIntent | None:
        """LLM-based classification fallback."""
        try:
            from biai.ai.prompt_templates import ROUTER_PROMPT
            prompt = ROUTER_PROMPT.format(question=question)
            response = self._vanna.submit_prompt(prompt)
            if not response:
                return None

            response_lower = response.strip().lower()
            if "process_diagram" in response_lower:
                return QueryIntent.PROCESS_DIAGRAM
            elif "hybrid" in response_lower:
                return QueryIntent.HYBRID
            else:
                return QueryIntent.SQL_QUERY
        except Exception as e:
            logger.warning("llm_router_failed", error=str(e))
            return None
```

### 4.3 Trigger patterns

| Pattern (PL) | Pattern (EN) | Intent |
|---------------|--------------|--------|
| "pokaz proces *" | "show process *" | PROCESS_DIAGRAM |
| "diagram *" | "diagram *" | PROCESS_DIAGRAM |
| "wizualizuj przebieg *" | "visualize flow *" | PROCESS_DIAGRAM |
| "etapy procesu *" | "process stages *" | PROCESS_DIAGRAM |
| "lejek sprzedazy" | "sales funnel" | PROCESS_DIAGRAM |
| "bottleneck w procesie *" | "bottleneck in process *" | HYBRID |
| "ile trwa etap *" | "how long does stage *" | HYBRID |
| "ile zamowien" | "how many orders" | SQL_QUERY |
| "sredni czas *" | "average time *" | SQL_QUERY |

---

## 5. Process Detector (Schema Analysis)

### 5.1 Cel

Automatyczne wykrywanie tabel procesowych w schemacie DB na podstawie heurystyk kolumnowych. Wyniki cachowane per `{db_type}:{schema_name}`.

### 5.2 Plik: `biai/ai/process_detector.py` (~200 LOC)

```python
"""Process Detector - identifies process tables in database schema."""

from dataclasses import dataclass, field

from biai.models.schema import SchemaSnapshot, TableInfo
from biai.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProcessTableInfo:
    """Detected process table with metadata."""
    table_name: str
    process_type: str       # "state_machine", "log", "pipeline", "approval"
    status_columns: list[str] = field(default_factory=list)
    timestamp_columns: list[str] = field(default_factory=list)
    from_to_columns: tuple[str, str] | None = None
    entity_fk_column: str | None = None
    actor_fk_column: str | None = None
    duration_column: str | None = None
    confidence: float = 0.0


@dataclass
class ProcessDefinition:
    """Complete process definition detected from schema."""
    name: str
    main_table: ProcessTableInfo
    history_table: ProcessTableInfo | None = None
    related_tables: list[str] = field(default_factory=list)
    view_name: str | None = None


class ProcessDetector:
    """Detects business process tables in database schema."""

    STATUS_PATTERNS = ["status", "state", "stage", "step", "phase",
                       "current_step", "current_status", "current_stage"]

    FROM_TO_PATTERNS = [
        ("from_status", "to_status"), ("from_state", "to_state"),
        ("from_stage", "to_stage"), ("previous_status", "new_status"),
    ]

    TIMESTAMP_PATTERNS = ["created_at", "updated_at", "changed_at",
                          "entered_at", "resolved_at", "completed_at"]

    DURATION_PATTERNS = ["duration", "duration_minutes", "duration_hours",
                         "resolution_minutes", "processing_time"]

    PROCESS_TABLE_NAMES = ["process_log", "pipeline", "workflow",
                           "approval", "ticket", "history"]

    def __init__(self):
        self._cache: dict[str, list[ProcessDefinition]] = {}

    def detect(self, schema: SchemaSnapshot) -> list[ProcessDefinition]:
        """Detect process tables in schema. Cached by schema_name."""
        cache_key = f"{schema.db_type}:{schema.schema_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        process_tables = []
        for table in schema.tables:
            info = self._analyze_table(table)
            if info and info.confidence >= 0.4:
                process_tables.append(info)

        definitions = self._group_into_processes(process_tables, schema)
        self._cache[cache_key] = definitions
        logger.info("process_detection_complete",
                     processes=len(definitions), tables=len(process_tables))
        return definitions

    def invalidate_cache(self):
        self._cache.clear()

    def get_process_table_names(self, schema: SchemaSnapshot) -> list[str]:
        """Flat list of process table names (for AgentRouter)."""
        defs = self.detect(schema)
        names = []
        for d in defs:
            names.append(d.main_table.table_name)
            if d.history_table:
                names.append(d.history_table.table_name)
        return names

    def _analyze_table(self, table: TableInfo) -> ProcessTableInfo | None:
        """Analyze single table for process patterns. Returns None if score=0."""
        col_names = [c.name.lower() for c in table.columns]
        score = 0.0
        info = ProcessTableInfo(table_name=table.name, process_type="unknown")

        # Table name check
        table_lower = table.name.lower()
        if any(p in table_lower for p in self.PROCESS_TABLE_NAMES):
            score += 0.3

        # Status/state columns
        for col in table.columns:
            cl = col.name.lower()
            if any(p == cl or cl.endswith(f"_{p}") for p in self.STATUS_PATTERNS):
                info.status_columns.append(col.name)
                score += 0.2

        # From/to transition columns
        for from_p, to_p in self.FROM_TO_PATTERNS:
            if from_p in col_names and to_p in col_names:
                info.from_to_columns = (
                    table.columns[col_names.index(from_p)].name,
                    table.columns[col_names.index(to_p)].name,
                )
                info.process_type = "state_machine"
                score += 0.4

        # Timestamp columns
        for col in table.columns:
            if any(p in col.name.lower() for p in self.TIMESTAMP_PATTERNS):
                info.timestamp_columns.append(col.name)
                score += 0.05

        # Duration columns
        for col in table.columns:
            if any(p in col.name.lower() for p in self.DURATION_PATTERNS):
                info.duration_column = col.name
                score += 0.15

        # FK columns
        for col in table.columns:
            if col.is_foreign_key:
                cl = col.name.lower()
                if any(k in cl for k in ["changed_by", "assigned_to", "approver"]):
                    info.actor_fk_column = col.name
                elif any(k in cl for k in ["order_id", "ticket_id", "request_id", "pipeline_id"]):
                    info.entity_fk_column = col.name

        # Determine process type
        if not info.from_to_columns:
            if info.status_columns and info.timestamp_columns:
                if "approval" in table_lower:
                    info.process_type = "approval"
                elif "pipeline" in table_lower:
                    info.process_type = "pipeline"
                else:
                    info.process_type = "log"

        info.confidence = min(score, 1.0)
        return info if score > 0.0 else None

    def _group_into_processes(
        self, tables: list[ProcessTableInfo], schema: SchemaSnapshot
    ) -> list[ProcessDefinition]:
        """Group detected tables into logical process definitions."""
        definitions = []
        used = set()
        tables.sort(key=lambda t: t.confidence, reverse=True)

        for table in tables:
            if table.table_name in used:
                continue
            # Find companion history table
            history = None
            for other in tables:
                if other.table_name in used or other.table_name == table.table_name:
                    continue
                if (table.entity_fk_column and other.entity_fk_column and
                    table.entity_fk_column.lower() == other.entity_fk_column.lower()):
                    history = other
                    break
            main = table
            if history and history.from_to_columns and not table.from_to_columns:
                main, history = history, table

            name = _humanize_table_name(main.table_name)

            # Find associated view
            view_name = None
            for t in schema.tables:
                tl = t.name.lower()
                if tl.startswith("v_") and any(
                    kw in tl for kw in main.table_name.lower().split("_") if len(kw) > 3
                ):
                    view_name = t.name
                    break

            defn = ProcessDefinition(name=name, main_table=main,
                                     history_table=history, view_name=view_name)
            used.add(main.table_name)
            if history:
                used.add(history.table_name)
            definitions.append(defn)

        return definitions


def _humanize_table_name(name: str) -> str:
    name = name.lower()
    for remove in ["_log", "_history", "_steps", "_process"]:
        name = name.replace(remove, "")
    return " ".join(p.capitalize() for p in name.split("_") if p)
```

### 5.3 Detekcja dla danych testowych

| Tabela | process_type | confidence | Kluczowe kolumny |
|--------|-------------|------------|------------------|
| ORDER_PROCESS_LOG | state_machine | 0.90 | from_status, to_status, duration_minutes |
| SALES_PIPELINE | pipeline | 0.55 | stage, entered_at |
| PIPELINE_HISTORY | state_machine | 0.70 | from/to pattern |
| SUPPORT_TICKETS | log | 0.50 | status, priority, timestamps |
| TICKET_HISTORY | state_machine | 0.70 | from/to pattern |
| APPROVAL_REQUESTS | approval | 0.50 | status, current_step |
| APPROVAL_STEPS | approval | 0.65 | step_name, status, timestamps |

---

## 6. Process Data Transformer

### 6.1 Cel

Konwersja danych procesowych (wyniki SQL) na format React Flow: `nodes[]` + `edges[]`.

### 6.2 Plik: `biai/ai/process_transformer.py` (~250 LOC)

```python
"""Process Data Transformer - converts SQL results to React Flow format."""

from dataclasses import dataclass, field
from typing import Any

import pandas as pd
from biai.ai.process_detector import ProcessDefinition
from biai.utils.logger import get_logger

logger = get_logger(__name__)

# ---- Node/edge type constants (matching custom React Flow nodes) ----
NODE_TYPE_START = "processStart"
NODE_TYPE_END = "processEnd"
NODE_TYPE_TASK = "processTask"
NODE_TYPE_GATEWAY = "processGateway"

# ---- Status -> Color mapping ----
STATUS_COLORS: dict[str, str] = {
    "delivered": "#22c55e", "closed": "#22c55e", "closed_won": "#22c55e",
    "approved": "#22c55e", "executed": "#22c55e", "resolved": "#22c55e",
    "closed_lost": "#ef4444", "rejected": "#ef4444", "cancelled": "#ef4444",
    "waiting_customer": "#eab308", "payment_pending": "#eab308", "pending": "#eab308",
    "in_progress": "#3b82f6", "in_transit": "#3b82f6", "investigating": "#3b82f6",
    "picking": "#3b82f6", "packing": "#3b82f6",
    "level1_review": "#a855f7", "level2_review": "#a855f7",
    "negotiation": "#a855f7", "proposal": "#a855f7",
    "default": "#6b7280",
}

# ---- Status -> Lucide icon mapping ----
STATUS_ICONS: dict[str, str] = {
    "order_placed": "shopping-cart", "payment_pending": "credit-card",
    "payment_confirmed": "check-circle", "warehouse_assigned": "warehouse",
    "picking": "package-search", "packing": "package",
    "shipped": "truck", "in_transit": "route", "delivered": "package-check",
    "lead": "user-plus", "qualified": "user-check",
    "proposal": "file-text", "negotiation": "handshake",
    "closed_won": "trophy", "closed_lost": "x-circle",
    "new": "plus-circle", "assigned": "user", "investigating": "search",
    "waiting_customer": "clock", "in_progress": "loader",
    "resolved": "check", "closed": "check-circle-2", "reopened": "refresh-cw",
    "draft": "file-edit", "submitted": "send",
    "level1_review": "eye", "level2_review": "shield-check",
    "approved": "thumbs-up", "rejected": "thumbs-down",
    "executed": "play-circle", "default": "circle",
}


@dataclass
class ProcessMetrics:
    """Metrics calculated from process data."""
    total_transitions: int = 0
    avg_duration_per_step: dict[str, float] = field(default_factory=dict)
    bottleneck_step: str | None = None
    bottleneck_duration: float = 0.0
    conversion_rates: dict[str, float] = field(default_factory=dict)
    current_distribution: dict[str, int] = field(default_factory=dict)


@dataclass
class ReactFlowData:
    """Data for React Flow component."""
    nodes: list[dict[str, Any]] = field(default_factory=list)
    edges: list[dict[str, Any]] = field(default_factory=list)
    metrics: ProcessMetrics = field(default_factory=ProcessMetrics)
    process_name: str = ""
    layout_direction: str = "TB"


class ProcessTransformer:
    """Transforms process data into React Flow nodes and edges."""

    def transform(
        self, df: pd.DataFrame, process_def: ProcessDefinition,
        layout_direction: str = "TB",
    ) -> ReactFlowData:
        """Transform DataFrame to React Flow data.

        For state_machine (from/to columns): builds graph from transitions
        For pipeline/log (status column): builds linear flow
        """
        main = process_def.main_table
        if main.from_to_columns:
            return self._transform_state_machine(df, process_def, layout_direction)
        return self._transform_status_based(df, process_def, layout_direction)

    def _transform_state_machine(
        self, df: pd.DataFrame, process_def: ProcessDefinition,
        layout_direction: str,
    ) -> ReactFlowData:
        """Transform state machine (from/to transitions) data."""
        from_col, to_col = process_def.main_table.from_to_columns
        from_found = _find_column(df, from_col)
        to_found = _find_column(df, to_col)
        if not from_found or not to_found:
            return ReactFlowData(process_name=process_def.name)

        # Extract unique states preserving order
        states = []
        seen = set()
        for _, row in df.iterrows():
            for col in [from_found, to_found]:
                val = str(row[col]).strip().lower()
                if val and val not in seen and val != "nan":
                    states.append(val)
                    seen.add(val)

        # Count outgoing transitions per state (for gateway detection)
        outgoing_count: dict[str, int] = {}
        for _, row in df.iterrows():
            src = str(row[from_found]).strip().lower()
            outgoing_count[src] = outgoing_count.get(src, 0) + 1

        # Build nodes
        nodes = []
        for i, state in enumerate(states):
            node_type = NODE_TYPE_TASK
            if i == 0:
                node_type = NODE_TYPE_START
            elif i == len(states) - 1:
                node_type = NODE_TYPE_END
            if outgoing_count.get(state, 0) > 1:
                node_type = NODE_TYPE_GATEWAY

            color = STATUS_COLORS.get(state, STATUS_COLORS["default"])
            icon = STATUS_ICONS.get(state, STATUS_ICONS["default"])
            nodes.append({
                "id": f"node-{state}",
                "type": node_type,
                "data": {
                    "label": _humanize_status(state),
                    "status": state,
                    "color": color,
                    "icon": icon,
                    "metrics": {},
                },
                "position": {"x": 0, "y": 0},  # layout recalculates
            })

        # Build edges with metrics
        edges = []
        metrics = ProcessMetrics()
        duration_col = _find_column(df, "avg_duration") or _find_column(df, "duration")
        count_col = _find_column(df, "transition_count") or _find_column(df, "count")

        for _, row in df.iterrows():
            from_state = str(row[from_found]).strip().lower()
            to_state = str(row[to_found]).strip().lower()
            if not from_state or not to_state or from_state == "nan":
                continue

            edge_label = ""
            edge_data: dict[str, Any] = {}

            if count_col and pd.notna(row.get(count_col)):
                count = int(row[count_col])
                edge_label = f"{count}x"
                edge_data["count"] = count
                metrics.total_transitions += count

            if duration_col and pd.notna(row.get(duration_col)):
                dur = float(row[duration_col])
                edge_data["duration"] = dur
                step_key = f"{from_state} -> {to_state}"
                metrics.avg_duration_per_step[step_key] = dur
                if dur > metrics.bottleneck_duration:
                    metrics.bottleneck_duration = dur
                    metrics.bottleneck_step = step_key
                dur_str = _format_duration(dur)
                edge_label = f"{edge_label} ({dur_str})" if edge_label else dur_str

            edges.append({
                "id": f"edge-{from_state}-{to_state}",
                "source": f"node-{from_state}",
                "target": f"node-{to_state}",
                "type": "smoothstep",
                "animated": True,
                "data": edge_data,
                "label": edge_label,
                "style": {"stroke": STATUS_COLORS.get(to_state, "#6b7280")},
            })

        # Mark bottleneck node
        if metrics.bottleneck_step:
            bn_to = metrics.bottleneck_step.split(" -> ")[-1]
            for node in nodes:
                if node["data"]["status"] == bn_to:
                    node["data"]["metrics"]["is_bottleneck"] = True
                    node["data"]["metrics"]["bottleneck_duration"] = (
                        _format_duration(metrics.bottleneck_duration)
                    )

        return ReactFlowData(
            nodes=nodes, edges=edges, metrics=metrics,
            process_name=process_def.name, layout_direction=layout_direction,
        )

    def _transform_status_based(
        self, df: pd.DataFrame, process_def: ProcessDefinition,
        layout_direction: str,
    ) -> ReactFlowData:
        """Transform status-based (no from/to) data into linear flow."""
        status_col = None
        for col_name in process_def.main_table.status_columns:
            found = _find_column(df, col_name)
            if found:
                status_col = found
                break
        if not status_col:
            for try_col in ["stage", "status", "step", "current_step"]:
                found = _find_column(df, try_col)
                if found:
                    status_col = found
                    break
        if not status_col:
            return ReactFlowData(process_name=process_def.name)

        statuses = [str(s).strip().lower() for s in df[status_col].dropna().unique() if str(s).strip()]
        count_col = _find_column(df, "count") or _find_column(df, "total")

        nodes, edges = [], []
        metrics = ProcessMetrics()

        for i, status in enumerate(statuses):
            node_type = NODE_TYPE_TASK
            if i == 0: node_type = NODE_TYPE_START
            elif i == len(statuses) - 1: node_type = NODE_TYPE_END

            color = STATUS_COLORS.get(status, STATUS_COLORS["default"])
            icon = STATUS_ICONS.get(status, STATUS_ICONS["default"])
            node_metrics = {}

            status_rows = df[df[status_col].str.lower().str.strip() == status]
            if not status_rows.empty and count_col:
                count_val = status_rows[count_col].iloc[0]
                if pd.notna(count_val):
                    node_metrics["count"] = int(count_val)
                    metrics.current_distribution[status] = int(count_val)

            nodes.append({
                "id": f"node-{status}", "type": node_type,
                "data": {"label": _humanize_status(status), "status": status,
                         "color": color, "icon": icon, "metrics": node_metrics},
                "position": {"x": 0, "y": 0},
            })
            if i < len(statuses) - 1:
                next_s = statuses[i + 1]
                edges.append({
                    "id": f"edge-{status}-{next_s}",
                    "source": f"node-{status}", "target": f"node-{next_s}",
                    "type": "smoothstep", "animated": True, "data": {},
                    "style": {"stroke": STATUS_COLORS.get(next_s, "#6b7280")},
                })

        return ReactFlowData(
            nodes=nodes, edges=edges, metrics=metrics,
            process_name=process_def.name, layout_direction=layout_direction,
        )


def _find_column(df: pd.DataFrame, name: str) -> str | None:
    name_lower = name.lower()
    for col in df.columns:
        if col.lower() == name_lower:
            return col
    return None

def _humanize_status(status: str) -> str:
    return status.replace("_", " ").title()

def _format_duration(minutes: float) -> str:
    if minutes < 60: return f"{minutes:.0f}m"
    elif minutes < 1440: return f"{minutes/60:.1f}h"
    else: return f"{minutes/1440:.1f}d"
```

### 6.3 SQL queries generowane dla procesow

**Format A: State Machine (from/to transitions)**
```sql
SELECT from_status, to_status,
       COUNT(*) AS transition_count,
       ROUND(AVG(duration_minutes), 1) AS avg_duration
FROM ORDER_PROCESS_LOG
GROUP BY from_status, to_status
ORDER BY transition_count DESC
```

**Format B: Status/Stage distribution**
```sql
SELECT stage, COUNT(*) AS total,
       ROUND(SUM(expected_value), 2) AS total_value
FROM SALES_PIPELINE
GROUP BY stage
```

---

## 7. Process Layout (Server-side)

### 7.1 Plik: `biai/ai/process_layout.py` (~80 LOC)

```python
"""Server-side layout calculation (Dagre-like topological sort)."""


def calculate_layout(
    nodes: list[dict], edges: list[dict],
    direction: str = "TB",
    node_width: int = 180, node_height: int = 60,
    rank_sep: int = 80, node_sep: int = 40,
) -> list[dict]:
    """Calculate node positions using topological sort + layered layout.

    Returns updated nodes with calculated positions.
    """
    # Build adjacency
    adj: dict[str, list[str]] = {}
    in_degree: dict[str, int] = {}
    node_ids = {n["id"] for n in nodes}

    for nid in node_ids:
        adj[nid] = []
        in_degree[nid] = 0

    for edge in edges:
        src, tgt = edge["source"], edge["target"]
        if src in adj and tgt in in_degree:
            adj[src].append(tgt)
            in_degree[tgt] = in_degree.get(tgt, 0) + 1

    # Kahn's algorithm -> layers
    layers: list[list[str]] = []
    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    visited = set()

    while queue:
        layers.append(queue[:])
        next_queue = []
        for nid in queue:
            visited.add(nid)
            for neighbor in adj.get(nid, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0 and neighbor not in visited:
                    next_queue.append(neighbor)
        queue = next_queue

    # Unvisited nodes (cycles) -> last layer
    unvisited = [nid for nid in node_ids if nid not in visited]
    if unvisited:
        layers.append(unvisited)

    # Assign positions
    pos: dict[str, dict] = {}
    for li, layer in enumerate(layers):
        for ni, nid in enumerate(layer):
            if direction == "TB":
                x = ni * (node_width + node_sep) - (len(layer) - 1) * (node_width + node_sep) / 2
                y = li * (node_height + rank_sep)
            else:
                x = li * (node_width + rank_sep)
                y = ni * (node_height + node_sep) - (len(layer) - 1) * (node_height + node_sep) / 2
            pos[nid] = {"x": x, "y": y}

    for node in nodes:
        if node["id"] in pos:
            node["position"] = pos[node["id"]]

    return nodes
```

---

## 8. React Flow Reflex Component

### 8.1 Struktura katalogu

```
biai/components/react_flow/
    __init__.py         # Exports
    wrapper.py          # rx.NoSSRComponent wrapping @xyflow/react
    process_flow.py     # High-level process_flow_card() component
```

### 8.2 Plik: `biai/components/react_flow/wrapper.py` (~100 LOC)

```python
"""React Flow wrapper for Reflex."""

import reflex as rx
from typing import Any


class ReactFlowLib(rx.NoSSRComponent):
    """Wrapper for @xyflow/react ReactFlow component."""
    library = "@xyflow/react@12.9.0"
    tag = "ReactFlow"

    nodes: rx.Var[list[dict[str, Any]]]
    edges: rx.Var[list[dict[str, Any]]]
    fit_view: rx.Var[bool] = True
    color_mode: rx.Var[str] = "dark"
    nodes_draggable: rx.Var[bool] = True
    nodes_connectable: rx.Var[bool] = False
    zoom_on_scroll: rx.Var[bool] = True
    pan_on_drag: rx.Var[bool] = True
    min_zoom: rx.Var[float] = 0.3
    max_zoom: rx.Var[float] = 2.0

    on_node_click: rx.EventHandler[lambda e, node: [node]]

    def _get_imports(self) -> dict:
        return {
            "@xyflow/react": [
                rx.ImportVar(tag="ReactFlow", is_default=True),
                rx.ImportVar(tag="Background"),
                rx.ImportVar(tag="Controls"),
                rx.ImportVar(tag="MiniMap"),
                rx.ImportVar(tag="ReactFlowProvider"),
            ],
        }

    def _get_custom_code(self) -> str:
        return "import '@xyflow/react/dist/style.css';"


class Background(rx.NoSSRComponent):
    library = "@xyflow/react@12.9.0"
    tag = "Background"
    variant: rx.Var[str] = "dots"
    gap: rx.Var[int] = 20
    size: rx.Var[int] = 1
    color: rx.Var[str] = "#333"


class Controls(rx.NoSSRComponent):
    library = "@xyflow/react@12.9.0"
    tag = "Controls"
    show_zoom: rx.Var[bool] = True
    show_fit_view: rx.Var[bool] = True
    show_interactive: rx.Var[bool] = False


class MiniMap(rx.NoSSRComponent):
    library = "@xyflow/react@12.9.0"
    tag = "MiniMap"
    node_stroke_color: rx.Var[str] = "#555"
    node_color: rx.Var[str] = "#333"


class ReactFlowProvider(rx.NoSSRComponent):
    library = "@xyflow/react@12.9.0"
    tag = "ReactFlowProvider"


# Convenience constructors
react_flow = ReactFlowLib.create
react_flow_background = Background.create
react_flow_controls = Controls.create
react_flow_minimap = MiniMap.create
react_flow_provider = ReactFlowProvider.create
```

**UWAGA:** Dokladna sygnatura NoSSRComponent moze wymagac dostosowania do Reflex 0.8.x API. Oficjalna dokumentacja Reflex (https://reflex.dev/docs/wrapping-react/example/) powinna byc referencja przy implementacji.

### 8.3 Custom Process Nodes (JS)

Custom node types rejestrowane przez `_get_custom_code()` w wrapper:

```javascript
// Injected via _get_custom_code() - registered as nodeTypes

const ProcessTaskNode = ({ data }) => {
  const isBottleneck = data.metrics?.is_bottleneck;
  return (
    <div style={{
      padding: '12px 20px', borderRadius: '8px',
      border: `2px solid ${data.color || '#6b7280'}`,
      background: `linear-gradient(135deg, ${data.color}15, ${data.color}08)`,
      color: '#e0e0e0', fontSize: '13px', fontWeight: 500,
      textAlign: 'center', minWidth: '140px',
      boxShadow: isBottleneck
        ? `0 0 15px ${data.color}60, 0 0 30px ${data.color}30`
        : `0 0 8px ${data.color}20`,
    }}>
      <div>{data.label}</div>
      {data.metrics?.count && (
        <div style={{fontSize:'11px',opacity:0.7,marginTop:4}}>{data.metrics.count} items</div>
      )}
      <Handle type="target" position="top" />
      <Handle type="source" position="bottom" />
    </div>
  );
};

const ProcessStartNode = ({ data }) => (
  <div style={{
    padding: '10px 24px', borderRadius: '24px',
    border: '2px solid #22c55e',
    background: 'linear-gradient(135deg, #22c55e15, #22c55e08)',
    color: '#e0e0e0', fontSize: '13px', fontWeight: 600,
    textAlign: 'center', boxShadow: '0 0 12px #22c55e30',
  }}>
    {data.label}
    <Handle type="source" position="bottom" />
  </div>
);

const ProcessEndNode = ({ data }) => (
  <div style={{
    padding: '10px 24px', borderRadius: '24px',
    border: `2px solid ${data.color || '#ef4444'}`,
    background: `linear-gradient(135deg, ${data.color}15, ${data.color}08)`,
    color: '#e0e0e0', fontSize: '13px', fontWeight: 600,
    textAlign: 'center', boxShadow: `0 0 12px ${data.color}30`,
  }}>
    {data.label}
    <Handle type="target" position="top" />
  </div>
);

const ProcessGatewayNode = ({ data }) => (
  <div style={{
    width: 50, height: 50, transform: 'rotate(45deg)',
    border: '2px solid #a855f7',
    background: 'linear-gradient(135deg, #a855f715, #a855f708)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    boxShadow: '0 0 12px #a855f730',
  }}>
    <div style={{transform:'rotate(-45deg)',color:'#e0e0e0',fontSize:11}}>{data.label}</div>
    <Handle type="target" position="top" style={{transform:'rotate(-45deg)'}} />
    <Handle type="source" position="bottom" style={{transform:'rotate(-45deg)'}} />
  </div>
);

const nodeTypes = {
  processTask: ProcessTaskNode,
  processStart: ProcessStartNode,
  processEnd: ProcessEndNode,
  processGateway: ProcessGatewayNode,
};
```

### 8.4 Glow Effects CSS

Dodac do `assets/styles/global.css`:

```css
/* React Flow dark theme overrides */
.react-flow { background: transparent !important; }
.react-flow__node { transition: box-shadow 0.3s ease, transform 0.2s ease; }
.react-flow__node:hover { transform: scale(1.05); z-index: 10 !important; }

/* Minimap + Controls dark theme */
.react-flow__minimap {
    background: rgba(0,0,0,0.4) !important;
    border: 1px solid var(--gray-a5); border-radius: 8px;
}
.react-flow__controls {
    background: rgba(30,30,30,0.8) !important;
    border: 1px solid var(--gray-a5); border-radius: 8px;
}
.react-flow__controls-button {
    background: transparent !important;
    border-color: var(--gray-a5) !important;
    fill: var(--gray-11) !important;
}

/* Bottleneck pulse animation */
@keyframes bottleneck-pulse {
    0%, 100% { box-shadow: 0 0 8px rgba(239, 68, 68, 0.3); }
    50% { box-shadow: 0 0 20px rgba(239, 68, 68, 0.6); }
}
```

### 8.5 Plik: `biai/components/react_flow/process_flow.py` (~120 LOC)

```python
"""Process Flow visualization card for dashboard."""

import reflex as rx
from biai.state.process import ProcessState
from biai.components.react_flow.wrapper import (
    react_flow, react_flow_background, react_flow_controls,
    react_flow_minimap, react_flow_provider,
)


def process_flow_card() -> rx.Component:
    """Process flow visualization card with React Flow."""
    return rx.box(
        # Header
        rx.hstack(
            rx.icon("workflow", size=16, color="var(--accent-9)"),
            rx.text(ProcessState.process_name, size="3", weight="bold"),
            rx.spacer(),
            rx.tooltip(
                rx.icon_button(
                    rx.icon("arrow-down-up", size=14),
                    variant="ghost", size="1",
                    on_click=ProcessState.toggle_layout,
                ),
                content="Toggle vertical/horizontal layout",
            ),
            width="100%", align="center",
            padding="8px 12px", border_bottom="1px solid var(--gray-a5)",
        ),
        # React Flow canvas
        rx.box(
            react_flow_provider(
                react_flow(
                    react_flow_background(variant="dots", gap=20, color="#333"),
                    react_flow_controls(show_zoom=True, show_fit_view=True),
                    react_flow_minimap(node_stroke_color="#555", node_color="#333"),
                    nodes=ProcessState.flow_nodes,
                    edges=ProcessState.flow_edges,
                    fit_view=True, color_mode="dark",
                    on_node_click=ProcessState.on_node_click,
                ),
            ),
            width="100%", height="400px",
            border_radius="8px", overflow="hidden",
        ),
        # Metrics bar
        rx.cond(
            ProcessState.has_metrics,
            rx.hstack(
                rx.cond(
                    ProcessState.bottleneck_label != "",
                    rx.hstack(
                        rx.icon("alert-triangle", size=14, color="#ef4444"),
                        rx.text("Bottleneck: ", size="1", color="var(--gray-10)"),
                        rx.text(ProcessState.bottleneck_label, size="1",
                                weight="bold", color="#ef4444"),
                        spacing="1", align="center",
                    ),
                ),
                rx.cond(
                    ProcessState.total_transitions > 0,
                    rx.hstack(
                        rx.icon("arrow-right-left", size=14, color="var(--gray-9)"),
                        rx.text(ProcessState.total_transitions_display,
                                size="1", color="var(--gray-10)"),
                        spacing="1", align="center",
                    ),
                ),
                width="100%", padding="8px 12px",
                border_top="1px solid var(--gray-a5)",
                spacing="4", flex_wrap="wrap",
            ),
        ),
        width="100%", border_radius="12px",
        bg="var(--gray-a2)", border="1px solid var(--gray-a5)",
        overflow="hidden",
    )
```

---

## 9. State Management

### 9.1 Plik: `biai/state/process.py` (~80 LOC)

```python
"""Process visualization state."""

from typing import Any
import reflex as rx


class ProcessState(rx.State):
    """Manages process visualization data for React Flow."""

    flow_nodes: list[dict[str, Any]] = []
    flow_edges: list[dict[str, Any]] = []
    process_name: str = ""
    show_process: bool = False
    layout_direction: str = "TB"
    bottleneck_label: str = ""
    total_transitions: int = 0
    flow_version: int = 0
    selected_node_id: str = ""
    selected_node_data: dict = {}

    def set_process_data(
        self, nodes: list[dict], edges: list[dict],
        process_name: str, bottleneck: str = "", transitions: int = 0,
    ):
        self.flow_nodes = nodes
        self.flow_edges = edges
        self.process_name = process_name
        self.show_process = True
        self.bottleneck_label = bottleneck
        self.total_transitions = transitions
        self.flow_version += 1

    def clear_process(self):
        self.flow_nodes = []
        self.flow_edges = []
        self.process_name = ""
        self.show_process = False
        self.bottleneck_label = ""
        self.total_transitions = 0
        self.selected_node_id = ""
        self.selected_node_data = {}
        self.flow_version += 1

    def toggle_layout(self):
        self.layout_direction = "LR" if self.layout_direction == "TB" else "TB"

    def on_node_click(self, node: dict):
        self.selected_node_id = node.get("id", "")
        self.selected_node_data = node.get("data", {})

    @rx.var
    def has_metrics(self) -> bool:
        return self.bottleneck_label != "" or self.total_transitions > 0

    @rx.var
    def total_transitions_display(self) -> str:
        return f"{self.total_transitions} transitions"
```

---

## 10. Modyfikacje Istniejacych Plikow

### 10.1 Podsumowanie

| # | Plik | Typ | Opis | LOC zmian |
|---|------|-----|------|-----------|
| 1 | `biai/state/chat.py` | MODIFY | Routing + process detection + ProcessState w `process_message()` | +60 |
| 2 | `biai/components/dashboard_panel.py` | MODIFY | Dodanie `process_flow_card()` | +15 |
| 3 | `biai/components/chat_message.py` | MODIFY | Badge "Process" (purple) | +10 |
| 4 | `biai/models/chart.py` | MODIFY | `ChartType.PROCESS_FLOW` | +1 |
| 5 | `biai/ai/prompt_templates.py` | MODIFY | `ROUTER_PROMPT` + `PROCESS_SQL_PROMPT` | +40 |

### 10.2 `biai/state/chat.py` - Szczegoly zmian

W `process_message()`, **PRZED** `result = await pipeline.process(question)` dodaj:

```python
# --- NOWY KOD: Agent routing ---
from biai.ai.agent_router import AgentRouter, QueryIntent
from biai.ai.process_detector import ProcessDetector
from biai.ai.process_transformer import ProcessTransformer
from biai.ai.process_layout import calculate_layout
from biai.state.process import ProcessState

router = AgentRouter(vanna_client=pipeline._vanna)
schema_snapshot = await pipeline.schema_manager.get_snapshot()
detector = ProcessDetector()
process_tables = detector.get_process_table_names(schema_snapshot)
intent = router.classify(question, process_tables)
```

**PO** sekcji z budowaniem chart (po linii ~205), dodaj:

```python
# --- NOWY KOD: Process visualization ---
if intent in (QueryIntent.PROCESS_DIAGRAM, QueryIntent.HYBRID):
    process_defs = detector.detect(schema_snapshot)
    if process_defs:
        best_process = _match_process_to_question(question, process_defs)
        if best_process:
            # Generate process-specific SQL
            from biai.ai.prompt_templates import PROCESS_SQL_PROMPT
            process_sql = _build_process_sql(best_process)
            proc_result = await pipeline._query_executor.execute(process_sql)

            if isinstance(proc_result, QueryResult):
                df_proc = proc_result.to_dataframe()
                transformer = ProcessTransformer()
                flow_data = transformer.transform(df_proc, best_process)
                flow_data.nodes = calculate_layout(
                    flow_data.nodes, flow_data.edges, direction="TB"
                )
                async with self:
                    process_state = await self.get_state(ProcessState)
                async with process_state:
                    process_state.set_process_data(
                        nodes=flow_data.nodes, edges=flow_data.edges,
                        process_name=flow_data.process_name,
                        bottleneck=flow_data.metrics.bottleneck_step or "",
                        transitions=flow_data.metrics.total_transitions,
                    )
else:
    # Clear process for non-process questions
    async with self:
        process_state = await self.get_state(ProcessState)
    async with process_state:
        process_state.clear_process()
```

**Nowe helper functions na koncu pliku:**

```python
def _match_process_to_question(
    question: str, process_defs: list
) -> "ProcessDefinition | None":
    """Match question to best process definition by keyword."""
    q_lower = question.lower()
    for defn in process_defs:
        name_words = defn.name.lower().split()
        table_words = defn.main_table.table_name.lower().replace("_", " ").split()
        all_words = set(name_words + table_words)
        if any(w in q_lower for w in all_words if len(w) > 3):
            return defn
    return process_defs[0] if process_defs else None


def _build_process_sql(process_def) -> str:
    """Build SQL for process data extraction."""
    main = process_def.main_table
    table = main.table_name

    if main.from_to_columns:
        from_col, to_col = main.from_to_columns
        dur_part = f", ROUND(AVG({main.duration_column}), 1) AS avg_duration" if main.duration_column else ""
        return (
            f"SELECT {from_col}, {to_col}, COUNT(*) AS transition_count{dur_part} "
            f"FROM {table} GROUP BY {from_col}, {to_col} "
            f"ORDER BY transition_count DESC"
        )
    elif main.status_columns:
        status_col = main.status_columns[0]
        return (
            f"SELECT {status_col}, COUNT(*) AS total "
            f"FROM {table} GROUP BY {status_col} "
            f"ORDER BY total DESC"
        )
    else:
        return f"SELECT * FROM {table} FETCH FIRST 100 ROWS ONLY"
```

### 10.3 `biai/components/dashboard_panel.py`

Dodaj import na gorze:
```python
from biai.state.process import ProcessState
from biai.components.react_flow.process_flow import process_flow_card
```

W `dashboard_panel()`, **miedzy** `chart_card()` a `data_table()`:
```python
# Process flow card (visibility via CSS)
rx.box(
    process_flow_card(),
    display=rx.cond(ProcessState.show_process, "block", "none"),
    width="100%",
),
```

### 10.4 `biai/components/chat_message.py`

Po badge "Chart" (linia ~63), dodaj:
```python
rx.cond(
    message.get("has_process", False),
    rx.badge(
        rx.icon("workflow", size=12),
        "Process",
        variant="surface",
        size="1",
        color_scheme="purple",
    ),
),
```

**UWAGA:** Nalezy tez dodac `"has_process": False` do kazdego message dict w `chat.py` (w `process_message()` przy tworzeniu wiadomosci user i assistant placeholder). Przy procesach: `"has_process": True`.

### 10.5 `biai/models/chart.py`

Dodaj do `ChartType`:
```python
PROCESS_FLOW = "process_flow"
```

### 10.6 `biai/ai/prompt_templates.py`

Dodaj na koncu pliku:

```python
ROUTER_PROMPT = """Classify the following user question into one of three categories:

1. SQL_QUERY - The user wants data, numbers, statistics, or comparisons
2. PROCESS_DIAGRAM - The user wants to see a business process visualization, workflow, or flow diagram
3. HYBRID - The user wants both data AND a process visualization

**Question:** {question}

Respond with ONLY one word: SQL_QUERY, PROCESS_DIAGRAM, or HYBRID
"""

PROCESS_SQL_PROMPT = """Based on the user's question about a business process, generate a SQL query
that retrieves process transition data suitable for visualization.

**Process:** {process_name}
**Main table:** {main_table} (type: {process_type})
{from_to_info}
{history_info}
**Available columns:** {columns}

**Question:** {question}

RULES:
1. If the table has from_status/to_status columns, GROUP BY them and COUNT(*).
   Include AVG(duration) if duration column exists.
2. If no from/to columns, GROUP BY the status/stage column and COUNT(*).
3. ORDER results logically.
4. Only SELECT statements.
5. Follow {dialect} dialect rules.

Generate ONLY the SQL query.
"""
```

---

## 11. Nowe Pliki - Podsumowanie

| # | Plik | LOC (szac.) | Opis |
|---|------|-------------|------|
| 1 | `biai/ai/agent_router.py` | ~120 | Klasyfikacja pytan (heuristic + LLM) |
| 2 | `biai/ai/process_detector.py` | ~200 | Wykrywanie tabel procesowych w schemacie DB |
| 3 | `biai/ai/process_transformer.py` | ~250 | DataFrame -> React Flow nodes/edges |
| 4 | `biai/ai/process_layout.py` | ~80 | Server-side topological sort layout |
| 5 | `biai/state/process.py` | ~80 | ProcessState (Reflex state) |
| 6 | `biai/components/react_flow/__init__.py` | ~10 | Exports |
| 7 | `biai/components/react_flow/wrapper.py` | ~100 | @xyflow/react NoSSRComponent wrapper |
| 8 | `biai/components/react_flow/process_flow.py` | ~120 | process_flow_card() UI component |
| | **RAZEM nowe pliki** | **~960 LOC** | |

**Zmiany w istniejacych plikach:** ~126 LOC
**Calkowity nowy kod:** ~1086 LOC
**Stosunek do istniejacego kodu:** 1086 / 3150 = ~34%

---

## 12. Dependency Graph Implementacji

### 12.1 Fazy

```
Faza 1: Backend Logic (2-3 dni)
  [1.1] models/chart.py           <- ChartType.PROCESS_FLOW
  [1.2] ai/process_detector.py    <- detekcja tabel procesowych
  [1.3] ai/agent_router.py        <- routing pytan
  [1.4] ai/prompt_templates.py    <- nowe szablony
  [1.5] Testy jednostkowe

Faza 2: Data Transformation (2-3 dni)
  [2.1] ai/process_transformer.py <- DataFrame -> nodes/edges
  [2.2] ai/process_layout.py      <- topological sort layout
  [2.3] state/process.py          <- ProcessState
  [2.4] Testy integracyjne

Faza 3: React Flow UI (3-4 dni)              <- ROWNOLEGLE z Faza 1+2
  [3.1] components/react_flow/__init__.py
  [3.2] components/react_flow/wrapper.py
  [3.3] components/react_flow/process_flow.py
  [3.4] CSS: glow effects, dark theme
  [3.5] Custom node types (JS)
  [3.6] Test wizualny z hardcoded data

Faza 4: Integration (2-3 dni)
  [4.1] state/chat.py             <- routing + process pipeline
  [4.2] components/dashboard_panel.py <- process_flow_card
  [4.3] components/chat_message.py <- badge "Process"
  [4.4] Test E2E z danymi testowymi Oracle (4 procesy)
```

### 12.2 Graf zaleznosci

```
[1.1] -> [1.2] -> [1.3]
               \
                -> [1.4]
                     |
                     v
              [2.1] -> [2.2] -> [2.3]
                                  |
[3.1] -> [3.2] -> [3.3]          |      <- Fazy 1-2 i 3 ROWNOLEGLE
                     |            |
                     v            v
                   [4.1] -------> [4.2] -> [4.3] -> [4.4]
```

**Krytyczna sciezka:** 1.1 -> 1.2 -> 2.1 -> 2.2 -> 2.3 -> 4.1 -> 4.4 = **7-9 dni**
**Z rownolegloscia (Faza 3 || Faza 1+2):** **7-10 dni roboczych**

---

## 13. Przykladowy Flow End-to-End

### Scenariusz: "Pokaz proces realizacji zamowien"

```
1. USER INPUT
   "Pokaz proces realizacji zamowien" -> ChatState.process_message()

2. AGENT ROUTING
   AgentRouter.classify() -> "pokaz proces" -> PROCESS_DIAGRAM

3. PROCESS DETECTION (z cache)
   ProcessDetector.detect(schema) -> [
     ProcessDefinition(name="Order Process",
       main_table=ProcessTableInfo(
         table="ORDER_PROCESS_LOG",
         from_to=("FROM_STATUS","TO_STATUS"),
         duration="DURATION_MINUTES",
         confidence=0.90))
   ]

4. PROCESS MATCHING
   _match_process("zamowien", defs) -> "Order Process"

5. SQL GENERATION
   _build_process_sql() ->
   SELECT FROM_STATUS, TO_STATUS, COUNT(*) AS TRANSITION_COUNT,
          ROUND(AVG(DURATION_MINUTES), 1) AS AVG_DURATION
   FROM ORDER_PROCESS_LOG
   GROUP BY FROM_STATUS, TO_STATUS
   ORDER BY TRANSITION_COUNT DESC

6. SQL EXECUTION
   QueryExecutor.execute() -> DataFrame (8+ rows)

7. DATA TRANSFORMATION
   ProcessTransformer.transform(df, process_def) -> ReactFlowData:
     nodes: 9 nodes (Start, 7 Tasks, End)
     edges: 8+ edges with counts and durations
     metrics: bottleneck = "packing" (avg 270 min)

8. LAYOUT
   calculate_layout(nodes, edges, "TB") -> positioned nodes

9. STATE UPDATE
   ProcessState.set_process_data(nodes, edges, "Order Process",
     bottleneck="packing -> shipped", transitions=1847)

10. UI RENDER
    dashboard_panel() -> process_flow_card():
    +----------------------------------------------+
    | [workflow icon] Order Process    [TB/LR btn]  |
    +----------------------------------------------+
    |                                              |
    |         +--[ Order Placed ]--+               |
    |                |  245x (15.2m)               |
    |         +--[ Payment Pending ]--+            |
    |                |  240x (22.5m)               |
    |         +--[ Payment Confirmed ]--+          |
    |                |  ...                        |
    |         +--[ PACKING !! ]--+     <- RED GLOW |
    |                |  210x (270.0m)              |
    |         +--[ Shipped ]--+                    |
    |                |  ...                        |
    |         +--[ Delivered ]--+                   |
    |                                              |
    |  [zoom] [fit] [minimap]                      |
    +----------------------------------------------+
    | ! Bottleneck: packing->shipped | 1847 trans  |
    +----------------------------------------------+

11. CHAT MESSAGE
    Badge: [SQL] [Data] [Process]
    Content: "Oto diagram procesu realizacji zamowien..."
```

---

## 14. NPM Dependencies

| Pakiet | Wersja | Cel | Instalacja |
|--------|--------|-----|------------|
| `@xyflow/react` | 12.9.0 | React Flow core | Automatycznie przez Reflex (NoSSRComponent `library` prop) |

Brak dodatkowych npm dependencies. Server-side layout eliminuje potrzebe `@dagrejs/dagre` po stronie JS.

---

## 15. Ryzyka i Mitygacje

| Ryzyko | P-stwo | Wplyw | Mitygacja |
|--------|--------|-------|-----------|
| React Flow NoSSRComponent wrap nie dziala z custom nodes | SREDNIE | WYSOKI | **Plan B:** Mermaid.js via `rx.html()` (statyczny, ale dziala). **Plan C:** Plotly `go.Sankey()` (juz zintegrowany) |
| Server-side layout niedokladny dla zlozonych grafow | NISKIE | SREDNI | Dodaj client-side `@dagrejs/dagre` jako fallback |
| Agent Router blednie klasyfikuje pytania | SREDNIE | SREDNI | LLM fallback + reczny override ("pokaz jako diagram") |
| Reflex 0.8.x zmienia API NoSSRComponent | NISKIE | WYSOKI | Pin wersji Reflex w requirements.txt |
| ProcessDetector false positives | NISKIE | NISKI | Confidence threshold (0.4) + process viz jest DODATKOWY (nie zastepuje chart/table) |

### Fallback strategies

**Plan B: Mermaid.js via rx.html()**
```python
def mermaid_diagram(code: str) -> rx.Component:
    return rx.html(f"""
        <div class="mermaid">{code}</div>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>mermaid.initialize({{theme: 'dark'}});</script>
    """)
```

**Plan C: Plotly Sankey (zero new dependencies)**
```python
import plotly.graph_objects as go
fig = go.Figure(go.Sankey(
    node=dict(label=[...], color=[...]),
    link=dict(source=[...], target=[...], value=[...]),
))
```

---

## 16. Checklist Implementacji

### Faza 1: Backend Logic
- [ ] Dodaj `ChartType.PROCESS_FLOW` do `biai/models/chart.py`
- [ ] Stworz `biai/ai/process_detector.py` (ProcessDetector, ProcessTableInfo, ProcessDefinition)
- [ ] Stworz `biai/ai/agent_router.py` (AgentRouter, QueryIntent)
- [ ] Dodaj `ROUTER_PROMPT`, `PROCESS_SQL_PROMPT` do `biai/ai/prompt_templates.py`
- [ ] Unit testy: detector (confidence scoring), router (classify patterns)

### Faza 2: Data Transformation
- [ ] Stworz `biai/ai/process_transformer.py` (ProcessTransformer, ReactFlowData, ProcessMetrics)
- [ ] Stworz `biai/ai/process_layout.py` (calculate_layout - topological sort)
- [ ] Stworz `biai/state/process.py` (ProcessState)
- [ ] Integration testy: mock DataFrame -> transformer -> layout -> state

### Faza 3: React Flow UI
- [ ] Stworz `biai/components/react_flow/__init__.py`
- [ ] Stworz `biai/components/react_flow/wrapper.py` (ReactFlowLib, Background, Controls, MiniMap)
- [ ] Stworz `biai/components/react_flow/process_flow.py` (process_flow_card)
- [ ] Custom node types (JS via _get_custom_code)
- [ ] CSS: glow effects, dark theme, bottleneck pulse (global.css)
- [ ] Visual test: render hardcoded process data

### Faza 4: Integration
- [ ] Modyfikuj `biai/state/chat.py` - routing + process pipeline + ProcessState
- [ ] Modyfikuj `biai/components/dashboard_panel.py` - dodaj process_flow_card
- [ ] Modyfikuj `biai/components/chat_message.py` - badge "Process"
- [ ] Dodaj `"has_process"` field do message dicts w chat.py
- [ ] E2E test: "Pokaz proces realizacji zamowien" -> diagram w UI
- [ ] E2E test: "Pokaz lejek sprzedazy" -> pipeline diagram
- [ ] E2E test: "Ile zamowien bylo" -> normalna sciezka SQL (bez diagramu)
- [ ] E2E test: 4 procesy z danych testowych Oracle

---

## 17. Zmiany Architekturalne vs Plan

> Sekcja dodana 2026-02-13 po zakonczeniu implementacji.

### 17.1 Elementy planu zastapione innymi rozwiazaniami

| Element z planu | Co zaimplementowano | Powod zmiany |
|----------------|---------------------|-------------|
| **AgentRouter** (`agent_router.py`) — pre-routing pytan SQL vs diagram | **ProcessDetector** (post-hoc) — pipeline ZAWSZE generuje SQL, procesy wykrywane w wynikach DataFrame | Uproszczenie: eliminacja bledu klasyfikacji, detekcja jest pewniejsza na danych niz na pytaniu |
| **ROUTER_PROMPT**, **PROCESS_SQL_PROMPT** w `prompt_templates.py` | Niepotrzebne — brak routera, SQL generowany standardowo przez Vanna | Routing nie jest potrzebny gdy detekcja jest post-hoc |
| **ProcessTransformer** (`process_transformer.py`, 250 LOC) | **ProcessGraphBuilder** (`process_graph_builder.py`, 313 LOC) — polaczony transformer + builder | Jedno przeznaczenie: budowanie grafu bezposrednio z DataFrame |
| Hardcoded **STATUS_COLORS** / **STATUS_ICONS** (60+ entries w transformer) | **DynamicStyler** (`dynamic_styler.py`) — algorytmiczne kolory/ikony | Skaluje sie na dowolne statusy bez recznego dodawania mappingow; 9 kategorii semantycznych + hash fallback |
| **ProcessDetector** (200 LOC, analiza schema) | **ProcessDetector** (91 LOC, analiza DataFrame) | Detekcja na wynikach SQL jest prostsza i pewniejsza niz analiza struktury tabel |

### 17.2 Nowe komponenty dodane (nie w oryginalnym planie)

| Komponent | Plik | Opis |
|-----------|------|------|
| **ProcessDiscoveryEngine** | `ai/process_discovery.py` | 7-krokowy pipeline auto-discovery procesow z schema i danych DB — wykrywa status columns, timestamps, FK chains + wzbogacanie LLM |
| **ProcessDiscoveryCache** | `ai/process_cache.py` | TTL cache (600s) dla wynikow discovery — unika powtarzania kosztownych skanow |
| **DynamicStyler** | `ai/dynamic_styler.py` | Algorytmiczne przypisywanie kolorow/ikon — 9 kategorii semantycznych, 60+ keywords, hash fallback |
| **DynamicProcessTrainer** | `ai/process_training_dynamic.py` | Generowanie dynamicznych training items z DiscoveredProcess dla Vanna |
| **process_training.py** | `ai/process_training.py` | Statyczne dane treningowe dla 4 typow procesow (order, sales, support, approval) |
| **ProcessMapState** + **process_map_card** | `state/process_map.py`, `components/process_map_card.py` | UI discovery: lista odkrytych procesow, przycisk "Discover Processes" |
| **models/discovery.py** | `models/discovery.py` | DiscoveredProcess, ColumnCandidate, TransitionPattern, EntityChain |
| **processCurrent** node type | `components/react_flow/wrapper.py` | Piaty typ wezla (nieplanowany) — wskazuje biezacy status w procesie |

### 17.3 Podsumowanie

Implementacja zachowala kluczowe decyzje architektoniczne:
- React Flow (@xyflow/react v12.9.0) jako technologia wizualizacji
- Server-side topological sort (Kahn's algorithm) zamiast client-side Dagre
- ProcessState z computed vars i version counter
- Pipeline integration (detekcja po etapie chart advisor)
- CSS glow effects, dark theme, bottleneck pulse animation
- Custom JS node types (5 zamiast planowanych 4)

Glowna zmiana koncepcyjna: **post-hoc detection** zamiast **pre-routing** — pipeline zawsze generuje SQL i wykonuje query, a dopiero w wynikach wykrywa dane procesowe. To eliminuje ryzyko blednej klasyfikacji pytan i upraszcza architekture.

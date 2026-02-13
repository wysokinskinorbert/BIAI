# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BIAI (Business Intelligence AI) is a local AI-powered chatbot that lets non-technical users query Oracle and PostgreSQL databases using natural language. Answers come as interactive Plotly charts, data tables, process flow diagrams, and streamed text descriptions. All AI inference runs locally via Ollama — no cloud LLM APIs.

## Commands

### Run the app
```bash
reflex run
```
The app starts at `http://localhost:3000`. Requires Ollama running at `localhost:11434`.

### Run tests
```bash
# All tests
pytest

# Single test file
pytest tests/test_sql_validator.py

# Single test
pytest tests/test_sql_validator.py::test_select_is_valid -v
```
Tests use `pytest` with `pytest-asyncio` (auto mode). Test config is in `pyproject.toml`.

### Docker test databases
```bash
docker compose -f docker-compose.dev.yml up -d
```
- PostgreSQL: `localhost:5433`, db=`biai_test`, user=`biai`, pass=`biai123`
- Oracle XE: `localhost:1521`, service=`XEPDB1`, user=`biai`, pass=`biai123`

Note: PostgreSQL uses port **5433** (not 5432) to avoid conflicts with local PostgreSQL.

### Install dependencies
```bash
pip install -e ".[dev]"
```

## Architecture

### Data Flow (question → answer)

```
User question → ChatState.process_message() [background task]
  → AIPipeline.process()
    → SelfCorrectionLoop (Vanna generates SQL, up to 5 retries)
      → SQLValidator (sqlglot AST: SELECT-only, keyword blocking, dialect transpilation)
      → QueryExecutor (runs SQL against DB, returns DataFrame)
    → ChartAdvisor (heuristic + LLM → ChartConfig)
    → ProcessDetector (optional: detect process flows in data)
  → AIPipeline.generate_description() (streams text via Ollama HTTP)
  → ChatState updates messages, QueryState, ChartState, ProcessState
```

### Layer Structure

| Layer | Directory | Key Classes |
|-------|-----------|-------------|
| **UI Components** | `biai/components/` | `layout.py` (split-screen), `chat_panel.py`, `dashboard_panel.py`, `sidebar.py` |
| **State (Reflex)** | `biai/state/` | `ChatState`, `DBState`, `QueryState`, `ChartState`, `ProcessState`, `SchemaState`, `BaseState` |
| **AI Pipeline** | `biai/ai/` | `AIPipeline`, `SelfCorrectionLoop`, `SQLValidator`, `ChartAdvisor`, `SchemaTrainer` |
| **Database** | `biai/db/` | `DatabaseConnector` (ABC), `PostgreSQLConnector`, `OracleConnector`, `SchemaManager`, `QueryExecutor` |
| **Models** | `biai/models/` | `ConnectionConfig`, `DBType`, `SQLQuery`, `QueryResult`, `ChartConfig`, `SchemaSnapshot` |
| **Config** | `biai/config/` | `constants.py` (all magic numbers), `settings.py` (pydantic-settings, `.env` support) |

### Key Integration: Vanna.ai

`MyVanna` (in `vanna_client.py`) inherits from both `ChromaDB_VectorStore` and `Ollama`. It uses RAG: schema DDL and example queries are trained into ChromaDB, then retrieved to build the SQL generation prompt. The `dialect` config param controls the system prompt ("You are a {dialect} expert"). Dialect-specific rules are injected via `static_documentation`.

### SQL Security (4 layers in `SQLValidator`)

1. **Blocked keywords** — regex word-boundary match against DML/DDL keywords
2. **Blocked patterns** — regex for injection patterns (`;`, `--`, `/*`, `INTO OUTFILE`)
3. **AST validation** — sqlglot parses SQL, verifies root node is `exp.Select`, walks tree for non-SELECT nodes
4. **Dialect transpilation** — `statement.sql(dialect=X)` converts e.g. `LIMIT 10` → `FETCH FIRST 10 ROWS ONLY` for Oracle

### Self-Correction Loop

`SelfCorrectionLoop` retries SQL generation up to `MAX_RETRIES` (5) times. On each failure (validation error or DB execution error), it feeds the error back to Vanna via `CORRECTION_PROMPT`. Refusal detection (LLM says "sorry, I can't...") triggers a fresh generation instead of correction.

## Reflex-Specific Patterns

- **Background tasks**: Use `@rx.event(background=True)`. State access requires `async with self:` blocks. Each `async with self:` is a separate lock acquisition — minimize work inside.
- **Cross-state access**: `async with self: other = await self.get_state(OtherState)` then `async with other:` to read/write. Always call `get_state()` inside `async with self`.
- **`_` prefix vars are NOT serialized**: Variables like `_connector`, `_cancel_requested` exist only in the current process. They are lost when state is loaded from the state store (e.g., in background tasks). Reconstruct from serialized fields instead.
- **Plotly charts**: Use `rx.plotly()` with trace data (list[dict]) and layout (dict). Build in `_build_plotly_figure()` in `chat.py`.
- **CSV download**: Computed `@rx.var csv_data` + `rx.download(data=QueryState.csv_data, filename=...)` in component `on_click`.

## Oracle vs PostgreSQL Considerations

- `DialectHelper` (`db/dialect.py`) provides dialect-specific rules, examples, and sqlglot dialect strings
- Oracle: `FETCH FIRST N ROWS ONLY` (not LIMIT), `NVL()`, `SYSDATE`, `TO_DATE()`, bind variable sanitization (`:param` → `'param'`)
- PostgreSQL: `LIMIT/OFFSET`, `COALESCE()`, `NOW()`, `::type` casting, `ILIKE`
- Schema defaults: PostgreSQL → `"public"`, Oracle → current user schema
- `QueryResult.to_dataframe()` applies `pd.to_numeric()` coercion for PostgreSQL `Decimal` columns

## Process Discovery (Dynamic)

When `USE_DYNAMIC_DISCOVERY=True` (default), `ProcessDiscoveryEngine` analyzes the schema for process-like patterns (status columns, timestamp sequences, FK chains). Discovered processes are cached at module level (`ProcessDiscoveryCache`) and used by `ProcessDetector` + `ProcessGraphBuilder` to generate React Flow diagrams. Layout is calculated by `calculate_layout()` in `process_layout.py`.

## Environment Configuration

Settings load from `.env` via `pydantic-settings` (`config/settings.py`). Key variables:
- `OLLAMA_HOST` (default: `http://localhost:11434`)
- `OLLAMA_MODEL` (default: `qwen2.5-coder:7b-instruct-q4_K_M`)
- `CHROMA_HOST`, `CHROMA_COLLECTION`
- `ORACLE_DSN`, `ORACLE_USER`, `ORACLE_PASSWORD`
- `POSTGRESQL_DSN`

## App Entry Points

- `biai/biai.py` — Reflex app instance, registers pages (`/` and `/settings`)
- `rxconfig.py` — Reflex config (app name, Tailwind, plugins)
- `biai/pages/index.py` → `main_layout()` → sidebar + chat panel (40%) + dashboard panel (60%)

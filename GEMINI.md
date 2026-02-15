# GEMINI.md - BIAI: Business Intelligence AI Agent Guide

BIAI is a local-first, AI-powered Business Intelligence analyst chatbot designed to query Oracle and PostgreSQL databases using natural language. It leverages local Large Language Models (LLM) via Ollama to ensure data privacy and zero cloud dependencies.

## 🚀 Quick Start & Commands

### Development Environment
```bash
# Install dependencies (editable mode with dev tools)
pip install -e ".[dev]"

# Start dev databases (PostgreSQL on 5433, Oracle XE on 1521)
docker compose -f docker-compose.dev.yml up -d

# Run the Reflex application
reflex run
```
The app starts at `http://localhost:3000`. Requires Ollama running at `localhost:11434`.

### Testing
```bash
# Run all tests (unit, integration, ai)
pytest

# Run specific test categories
pytest -m integration  # Requires Docker DBs
pytest -m ai_questions # Requires Ollama + Docker DBs

# Test a specific component
pytest tests/test_sql_validator.py
```

## 🏗️ System Architecture

BIAI follows a modular, layered architecture implemented in pure Python.

### Directory & Layer Structure

| Layer | Directory | Key Classes / Responsibility |
|-------|-----------|-----------------------------|
| **UI Layer** | `biai/components/` | `layout.py` (split-screen), `chat_panel.py`, `dashboard_panel.py` |
| **State Layer** | `biai/state/` | `ChatState`, `DBState`, `QueryState`, `ChartState`, `ProcessState` |
| **AI Pipeline** | `biai/ai/` | `AIPipeline`, `SelfCorrectionLoop`, `SQLValidator`, `ProcessDiscoveryEngine` |
| **Data Layer** | `biai/db/` | `DatabaseConnector`, `PostgreSQLConnector`, `OracleConnector`, `QueryExecutor` |
| **Models** | `biai/models/` | Pydantic definitions for `Connection`, `SQLQuery`, `ChartConfig`, `Insight` |
| **Config** | `biai/config/` | `constants.py` (all magic numbers), `settings.py` (pydantic-settings) |

### AI Pipeline Flow
1. **User Question** → `ChatState.process_message()` (Background Event).
2. **Context Enrichment** → Last 5 exchanges injected into prompt.
3. **Multi-Step Planning** → `AnalysisPlanner` decomposes complex tasks.
4. **Self-Correction Loop** → Vanna generates SQL (up to 5 retries).
5. **SQL Security Validation** → 4-Layer `SQLValidator` (Regex + AST + Transpilation).
6. **Execution** → `QueryExecutor` returns `pd.DataFrame`.
7. **Post-Process** → `ChartAdvisor` (Viz) + `InsightAgent` (Stats) + `ProcessDetector` (BPMN).
8. **Description** → Streamed natural language summary via Ollama.

## 🛡️ SQL Security & Guardrails

The `SQLValidator` implements 4 critical security layers:
1. **Blocked Keywords:** Regex-based word boundary matching for DML/DDL (DROP, TRUNCATE, DELETE).
2. **Blocked Patterns:** Detection of injection attempts (`;`, `--`, `/*`, `INTO OUTFILE`).
3. **AST Validation:** `sqlglot` verifies the root node is `exp.Select` and no dangerous nodes exist in the tree.
4. **Dialect Transpilation:** Safe conversion of syntax (e.g., `LIMIT` vs `FETCH FIRST`) using `sqlglot.transpile`.

## ⚡ Reflex-Specific Patterns (CRITICAL)

- **Background Tasks:** Use `@rx.event(background=True)`. State access requires `async with self:` locks.
- **Cross-State Access:** Call `get_state(OtherState)` inside `async with self:`, then use `async with other_state:`.
- **Serialization Caveat:** Variables prefixed with `_` (e.g., `_connector`) are **NOT** serialized and will be lost across background tasks or session restarts. Re-initialize them from persistent fields.
- **CSV Handling:** Uses computed `@rx.var csv_data` + `rx.download()` for seamless export.

## 🗄️ Database Dialect Nuances

### Oracle Considerations
- Uses `FETCH FIRST N ROWS ONLY` instead of `LIMIT`.
- Case-sensitivity rules in column names (often uppercase).
- `DialectHelper` injects specific rules like `NVL()`, `SYSDATE`, and `TO_DATE()`.

### PostgreSQL Considerations
- Default schema is `"public"`.
- Supports `LIMIT/OFFSET`, `COALESCE()`, and `NOW()`.
- Numeric coercion: `QueryResult.to_dataframe()` automatically converts `Decimal` to numeric types.

## 🧠 Dynamic Process Mining

When `USE_DYNAMIC_DISCOVERY=True`:
- `ProcessDiscoveryEngine` scans for status patterns, FK chains, and historical tables.
- Discovered workflows are cached at module level in `ProcessDiscoveryCache`.
- Visualization uses **React Flow** with custom layout logic (`process_layout.py`) based on topological sorting.

## ⚙️ Environment Configuration (`.env`)

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b-instruct-q4_K_M` | Primary SQL model |
| `CHROMA_HOST` | `None` (Local) | Vector DB host |
| `POSTGRESQL_DSN` | - | Full DSN for PostgreSQL |
| `ORACLE_DSN` | - | Full DSN for Oracle XE |
| `QUERY_TIMEOUT` | `30` | Execution timeout in seconds |
| `ROW_LIMIT` | `1000` | Safety limit for UI result sets |

# BIAI Application Analysis Report

**Date:** 2026-02-14
**Scope:** Complete codebase analysis, feature inventory, architecture review, gap analysis
**Codebase:** 15,358 LOC (application) + 3,104 LOC (tests) across ~90 Python files

---

## 1. Codebase Structure

### Directory Layout

```
biai/
  biai.py                  # App entry point (Reflex app instance, 4 pages)
  config/
    constants.py           # All magic numbers, limits, blocked SQL keywords
    settings.py            # pydantic-settings, .env loading
  state/                   # 15 Reflex state classes
    base.py                # BaseState (sidebar control)
    database.py            # DBState (connection lifecycle, reconnection)
    chat.py                # ChatState (main orchestrator, ~590 lines)
    query.py               # QueryState (SQL display, pagination, CSV export)
    chart.py               # ChartState (dual engine: ECharts + Plotly)
    schema.py              # SchemaState (explorer, profiling, glossary, ERD)
    process.py             # ProcessState (flow visualization, edit mode)
    process_map.py         # ProcessMapState (discovery from DB schema)
    dashboard.py           # DashboardState (builder, templates, persistence)
    model.py               # ModelState (Ollama model selector)
    pinned.py              # PinnedState (pin results to dashboard)
    saved_queries.py       # SavedQueriesState (favorites, query storage)
    presets.py             # PresetsState (connection presets, encrypted passwords)
    query_builder.py       # QueryBuilderState (visual SQL builder, ~446 lines)
  ai/                      # AI pipeline (25 files)
    pipeline.py            # AIPipeline orchestrator (~542 lines)
    vanna_client.py        # MyVanna (ChromaDB + Ollama), RAG-based SQL gen
    sql_validator.py       # 4-layer SQL security (keywords, patterns, AST, transpile)
    self_correction.py     # Retry loop (up to 5 attempts with error feedback)
    chart_advisor.py       # Heuristic + LLM chart recommendation (~349 lines)
    echarts_builder.py     # ECharts option builder, 13 chart types (~970 lines)
    chart_builder.py       # Plotly chart builder (fallback)
    insight_agent.py       # Statistical insights (Pareto, anomaly, trend, correlation)
    storyteller.py         # Data narratives via LLM
    analysis_planner.py    # Multi-step query decomposition
    analysis_executor.py   # Executes decomposed analysis steps
    process_discovery.py   # Dynamic business process discovery from schema
    process_detector.py    # Detects processes in query results
    process_layout.py      # Graph layout calculation for process flows
    process_cache.py       # Module-level cache for discovered processes
    process_training.py    # Static process training for Vanna
    process_training_dynamic.py  # Dynamic process training
    data_profiler.py       # Auto-profiling engine (semantic types, anomalies)
    business_glossary.py   # AI-generated business glossary
    training.py            # SchemaTrainer (trains Vanna with schema + examples)
    dynamic_styler.py      # Dynamic ECharts styling
    prompt_templates.py    # All LLM prompt templates (10 prompts)
  db/                      # Database abstraction
    base.py                # DatabaseConnector ABC
    postgresql.py          # asyncpg-based PostgreSQL connector
    oracle.py              # oracledb-based Oracle connector
    dialect.py             # DialectHelper (rules, examples, sqlglot dialect mapping)
    schema_manager.py      # SchemaManager (snapshot, tables, columns)
    query_executor.py      # QueryExecutor (runs SQL, returns QueryResult)
  models/                  # Pydantic models
    connection.py          # ConnectionConfig, DBType (ORACLE|POSTGRESQL)
    schema.py              # SchemaSnapshot, TableInfo, ColumnInfo
    query.py               # SQLQuery, QueryResult, QueryError
    chart.py               # ChartType (16 types), ChartEngine, ChartConfig
    message.py             # ChatMessage (role, content, badges, insights)
    process.py             # ProcessFlow, ProcessNode, ProcessEdge
    discovery.py           # DiscoveredProcess, TransitionPattern, EntityChain
    profile.py             # ColumnProfile, TableProfile, SemanticType, Anomaly
    glossary.py            # GlossaryEntry, TableGlossary
    analysis.py            # AnalysisPlan, AnalysisStep
    insight.py             # Insight model
    story.py               # DataStory model (context, findings, implications)
  components/              # UI components
    layout.py              # Split-screen: sidebar(280px) + chat(40%) + dashboard(60%)
    chat_panel.py          # Chat interface with input, messages, suggestions
    dashboard_panel.py     # Dashboard with charts, tables, KPIs, process flows
    sidebar.py             # Sidebar: connection, explorer, settings tabs
    chat_message.py        # Message bubble (badges, insights, story, retry)
    chart_card.py          # Dual-engine chart rendering (ECharts/Plotly)
    data_table.py          # Sortable, paginated data table
    data_explorer.py       # Schema explorer with profiling + glossary
    model_selector.py      # Ollama model dropdown
    connection_form.py     # DB connection form
    connection_presets.py  # Preset management UI
    kpi_card.py            # Single-value KPI display
    process_map_card.py    # Process map visualization
    erd_diagram.py         # ERD schema visualization (React Flow)
    schema_explorer.py     # Schema tree component
    react_flow/            # React Flow wrappers
      wrapper.py           # Base React Flow component
      process_flow.py      # Process flow nodes/edges
      process_comparison.py # Side-by-side process comparison
    echarts/               # ECharts wrapper
      wrapper.py           # Custom ECharts Reflex component
    dashboard_builder/     # Dashboard builder components
      builder_page.py      # /dashboard page layout
      grid_layout.py       # react-grid-layout integration
      widget.py            # Widget rendering (chart, table, kpi, text, insight)
    query_builder/         # Query builder components
      builder_view.py      # /builder page with visual SQL composition
  pages/                   # Route definitions
    index.py               # / — main layout (chat + dashboard)
    settings.py            # /settings — connection, model, system settings
    dashboard.py           # /dashboard — dashboard builder
    query_builder.py       # /builder — visual SQL builder
  utils/                   # Utilities
    logger.py              # structlog-based logging
    crypto.py              # Fernet encryption for connection passwords
    connection_storage.py  # Persists connection presets to disk
    query_storage.py       # Persists saved queries to disk
    dashboard_storage.py   # Persists dashboard layouts to disk
  tests/                   # 20 test files, 3,104 LOC
```

### Lines of Code Distribution

| Layer | Files | Approx. LOC | % of Total |
|-------|-------|-------------|-----------|
| State | 15 | ~4,200 | 27% |
| AI Pipeline | 25 | ~5,100 | 33% |
| Components | 20+ | ~3,500 | 23% |
| DB / Models | 15 | ~1,800 | 12% |
| Config / Utils | 8 | ~750 | 5% |
| **Total** | **~90** | **15,358** | **100%** |

---

## 2. Feature Inventory

### 2.1 Core Features

| Feature | Status | Details |
|---------|--------|---------|
| Natural language to SQL | WORKING | Vanna.ai RAG + Ollama local LLM |
| Multi-database support | WORKING | PostgreSQL (asyncpg) + Oracle (oracledb) |
| SQL validation (4 layers) | WORKING | Keywords, patterns, AST (sqlglot), dialect transpilation |
| Self-correction loop | WORKING | Up to 5 retries with error feedback to LLM |
| Dialect transpilation | WORKING | LIMIT -> FETCH FIRST (Oracle), etc. via sqlglot |
| Query execution | WORKING | Timeout (30s default), row limit (10,000), read-only enforcement |
| Refusal detection | WORKING | Regex-based detection of LLM refusals, fresh re-generation |
| Bind variable sanitization | WORKING | Oracle `:param` -> `'param'` literal |

### 2.2 Visualization Features

| Feature | Status | Details |
|---------|--------|---------|
| ECharts charts (primary) | WORKING | 13 types: bar, line, area, scatter, pie, gauge, funnel, heatmap, waterfall, treemap, sunburst, radar, parallel |
| Plotly charts (fallback) | WORKING | Fallback when ECharts fails |
| Chart type auto-detection | WORKING | Heuristic-based with LLM fallback |
| Chart annotations | WORKING | min/max markPoints, average markLine, trend line (linear regression), anomaly regions |
| Dark theme styling | WORKING | Consistent dark palette across all chart types |
| Fullscreen chart view | WORKING | Dialog-based maximize |
| Dynamic chart height | WORKING | Adjusts based on data row count |
| Chart engine badge | WORKING | Shows "ECharts" or "Plotly" indicator |

### 2.3 Data Features

| Feature | Status | Details |
|---------|--------|---------|
| Sortable data tables | WORKING | Click column headers, toggle asc/desc |
| Pagination | WORKING | 15 rows/page with navigation |
| CSV export | WORKING | Via computed var + rx.download |
| KPI cards | WORKING | Auto-detected for single-row, <= 4 columns |
| Data profiling | WORKING | Semantic type detection, null%, distinct count, top values, anomalies |
| Business glossary | WORKING | AI-generated table/column descriptions |
| ERD diagram | WORKING | React Flow visualization of schema relationships |

### 2.4 Process Mining Features

| Feature | Status | Details |
|---------|--------|---------|
| Dynamic process discovery | WORKING | From status columns, transition tables, FK chains |
| Process flow visualization | WORKING | React Flow with custom node types |
| Process editing | WORKING | Add/delete/move nodes, edit labels, change colors, undo/redo |
| Process comparison | WORKING | Side-by-side comparison view |
| Token animation | WORKING | Animated flow along edges |
| Layout toggle | WORKING | Top-Bottom / Left-Right |
| Process-aware SQL training | WORKING | Injects process knowledge into Vanna |

### 2.5 Advanced Analytics

| Feature | Status | Details |
|---------|--------|---------|
| Multi-step analysis | WORKING | AnalysisPlanner decomposes complex questions |
| Statistical insights | WORKING | Pareto (80/20), anomaly (z-score), trend, correlation, distribution skew |
| Data storytelling | WORKING | LLM-generated narratives (context, findings, implications, recommendations) |
| Multi-turn conversation | WORKING | Last 5 exchanges as context |
| Follow-up suggestions | WORKING | Pattern-based query suggestions |
| Categorical value discovery | WORKING | Auto-discovers DISTINCT values for status/type columns |

### 2.6 Infrastructure Features

| Feature | Status | Details |
|---------|--------|---------|
| Connection presets | WORKING | CRUD with Fernet-encrypted passwords, persisted to disk |
| Saved queries (favorites) | WORKING | Persist and re-run, with query storage |
| Pinned results | WORKING | Pin chart+table to mini-dashboard grid |
| Dashboard builder | WORKING | Widget-based grid layout, 4 templates, persistence |
| Visual SQL builder | WORKING | Block-based (table, filter, aggregate, join, sort, limit) via React Flow |
| Ollama model selector | WORKING | List models from API, set as default |
| Schema selector | WORKING | Switch schemas on connected database |
| Connection read-only check | WORKING | Validates SELECT-only permissions |

---

## 3. Architecture Analysis

### 3.1 Data Flow

```
User Question (chat input)
    |
    v
ChatState.process_message() [background task]
    |
    +--> DBState.get_connector() [cross-state, reconnects if needed]
    |
    +--> AIPipeline.train_schema() [lazy, once per connection]
    |       |
    |       +--> SchemaManager.get_snapshot()
    |       +--> DialectHelper.get_documentation()
    |       +--> DialectHelper.get_examples()
    |       +--> ProcessDiscoveryEngine.discover() [if dynamic discovery enabled]
    |       +--> get_categorical_columns() + DISTINCT queries
    |       +--> Vanna.train() [DDL, docs, examples into ChromaDB]
    |
    +--> AIPipeline.process()
    |       |
    |       +--> AnalysisPlanner.plan() [checks if multi-step needed]
    |       |
    |       +--> [Single-step path]:
    |       |       +--> SelfCorrectionLoop.run()
    |       |       |       +--> Vanna.generate_sql() [RAG: retrieve + LLM]
    |       |       |       +--> SQLValidator.validate() [4 layers]
    |       |       |       +--> QueryExecutor.execute() [async, timeout]
    |       |       |       +--> [on error: retry with CORRECTION_PROMPT]
    |       |       |
    |       |       +--> ChartAdvisor.recommend() [heuristic + LLM fallback]
    |       |       +--> ProcessDetector.detect() [optional]
    |       |
    |       +--> [Multi-step path]:
    |               +--> AnalysisExecutor.execute_plan()
    |               +--> Combine results (concat DataFrames)
    |
    +--> ChatState._build_chart() [ECharts -> Plotly fallback, 3 attempts]
    +--> ChatState._build_process_flow() [React Flow nodes/edges]
    +--> AIPipeline.generate_description() [streaming via Ollama HTTP]
    +--> InsightAgent.generate_insights() [ThreadPoolExecutor, 10s timeout]
    +--> DataStoryteller.create_story() [if story_mode enabled]
    |
    v
UI updates: ChatState, QueryState, ChartState, ProcessState
```

### 3.2 State Architecture

```
rx.State (Reflex base)
    |
    +--> BaseState
    |       sidebar_open, sidebar_section
    |
    +--> DBState
    |       connection config, connector lifecycle, __getstate__ override
    |
    +--> ChatState (main orchestrator, ~590 lines)
    |       messages, conversation_context, insights, analysis_steps
    |       story_mode, story_data, follow-up suggestions
    |
    +--> QueryState
    |       sql, columns, rows, pagination, sorting, CSV export, KPI detection
    |
    +--> ChartState
    |       plotly_fig_data, echarts_option, chart_version, fullscreen
    |
    +--> SchemaState (~597 lines)
    |       schema snapshot, profiling, glossary, ERD, schema selector
    |
    +--> ProcessState (~363 lines)
    |       nodes/edges, edit mode (undo/redo), comparison, token animation
    |
    +--> ProcessMapState
    |       discovery results from database schema
    |
    +--> DashboardState (~473 lines)
    |       widgets, grid layout, templates, persistence
    |
    +--> ModelState
    |       available models, current model, set-as-default
    |
    +--> PinnedState
    |       pinned chart+table results
    |
    +--> SavedQueriesState
    |       favorites, query storage
    |
    +--> PresetsState
    |       connection presets, encrypted passwords
    |
    +--> QueryBuilderState (~446 lines)
            visual blocks, SQL generation from graph
```

**Total: 15 state classes** managing orthogonal concerns with cross-state communication via `get_state()`.

### 3.3 Security Model (SQL Injection Prevention)

```
Layer 1: BLOCKED_KEYWORDS (14 terms)
    INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, GRANT, REVOKE,
    EXEC, EXECUTE, MERGE, DBMS_, UTL_

Layer 2: BLOCKED_PATTERNS (6 regex patterns)
    ; (multiple statements), -- (comments), /* */ (block comments),
    INTO OUTFILE/DUMPFILE, xp_ (SQL Server), INFORMATION_SCHEMA write patterns

Layer 3: AST VALIDATION (sqlglot)
    - Parse SQL into AST
    - Verify root is SELECT | UNION | INTERSECT | EXCEPT
    - Walk entire tree for Insert, Update, Delete, Drop, Create, Alter nodes

Layer 4: DIALECT TRANSPILATION
    - sqlglot transpiles to target dialect
    - e.g., LIMIT 10 -> FETCH FIRST 10 ROWS ONLY (Oracle)
    - Ensures syntactically correct output for target DB

Additional: Oracle bind variable sanitization (:param -> 'param')
```

### 3.4 Technology Stack

| Component | Technology | Version/Notes |
|-----------|-----------|---------------|
| Web Framework | Reflex | 0.8.x (Python fullstack) |
| Frontend | React (via Reflex) | Auto-generated from Python components |
| Styling | Tailwind CSS | Dark theme, violet accent |
| Charts (primary) | Apache ECharts | 13 chart types, custom dark theme |
| Charts (fallback) | Plotly | Via rx.plotly() |
| Process Flows | React Flow | Custom node types, layout calculation |
| Dashboard Grid | react-grid-layout | Widget-based grid layout |
| SQL AI | Vanna.ai | RAG: ChromaDB + Ollama |
| Vector Store | ChromaDB | Local persistent, path: ~/.biai/chromadb/ |
| LLM | Ollama | Local inference, default: qwen3-coder:30b |
| PostgreSQL Driver | asyncpg | Async native PostgreSQL |
| Oracle Driver | oracledb | Python-oracledb (thin mode) |
| SQL Parser | sqlglot | AST validation + dialect transpilation |
| Data Processing | Pandas | DataFrame operations, CSV export |
| Models | Pydantic | Data validation, serialization |
| Config | pydantic-settings | .env file loading |
| Encryption | cryptography (Fernet) | Connection password encryption |
| Logging | structlog | Structured JSON logging |
| Testing | pytest + pytest-asyncio | 20 test files, 3,104 LOC |

---

## 4. UI/UX Assessment

### 4.1 Layout Architecture

```
+--[SIDEBAR 280px]--+---[CHAT PANEL 40%]---+---[DASHBOARD PANEL 60%]---+
|                    |                       |                            |
| [BIAI Logo]        | [Header: Story/Save]  | [Header: Pin/CSV/Build]   |
| [Connection Tab]   | [Saved Queries Panel]  | [KPI Card (if detected)]  |
| [Explorer Tab]     | [Message List]         | [Chart Card (ECharts)]    |
| [Settings Tab]     |   - User bubble        | [Process Flow Card]       |
|                    |   - AI bubble          | [Data Table (paginated)]  |
| [Schema Tree]      |     - SQL badge        | [SQL Viewer]              |
| [Profiling Btn]    |     - Chart badge      | [Pinned Results Grid]     |
| [Glossary Btn]     |     - Insights         |                            |
| [ERD Btn]          |     - Story section    | [Default Dashboard]       |
|                    | [Suggestion Chips]     | [Empty State]             |
| [Connection Status]| [Input + Send/Stop]    |                            |
+--------------------+-----------------------+----------------------------+
```

### 4.2 Pages

| Route | Purpose | Key Components |
|-------|---------|---------------|
| `/` | Main app | Sidebar + Chat (40%) + Dashboard (60%) |
| `/settings` | Settings page | Connection, model, system settings |
| `/dashboard` | Dashboard builder | Grid layout builder with templates |
| `/builder` | Query builder | Visual block-based SQL composition |

### 4.3 UI Strengths

1. **Split-screen layout** is effective for chat+results paradigm
2. **Dark theme** is consistently applied across all components
3. **ECharts integration** provides rich, interactive visualizations
4. **Real-time streaming** of LLM descriptions token-by-token
5. **Follow-up suggestions** guide users to next questions
6. **Badges** (SQL, Data, Chart, Process) clearly indicate what each response contains
7. **Collapsible sidebar** maximizes content area when not needed
8. **Multiple result views** (chart, table, KPI, process flow) adapt to data type
9. **Schema explorer** with search, profiling, and glossary is powerful for data discovery

### 4.4 UI Weaknesses / Issues

1. **No responsive design** — fixed percentages (40%/60%) break on small screens
2. **No mobile layout** — sidebar + split-screen doesn't work on mobile
3. **Limited keyboard navigation** — no keyboard shortcuts documented
4. **No theme toggle** — dark-only, no light theme option
5. **Chat history not persistent** — messages lost on page refresh (Reflex state reset)
6. **No loading skeleton variety** — same skeleton for all content types
7. **Dashboard builder requires separate page** — context switch from main chat
8. **Query builder disconnected** — separate /builder page, not integrated into chat flow
9. **No drag-and-drop** for chart customization
10. **Limited error messaging** — technical DB errors sometimes leak to UI despite `_friendly_error()`

---

## 5. Gap Analysis vs Modern BI Systems

### Compared to: Metabase, Superset, Power BI, Tableau, ThoughtSpot

| Capability | BIAI Status | Modern BI Standard | Gap Level |
|-----------|-------------|-------------------|-----------|
| Natural language queries | IMPLEMENTED | ThoughtSpot-level NLQ | LOW |
| Multi-database | IMPLEMENTED (2) | 20+ connectors typical | HIGH |
| Chart types | IMPLEMENTED (16) | 30-50 types typical | MEDIUM |
| Dashboard building | IMPLEMENTED (basic) | Full drag-drop builder | MEDIUM |
| Report scheduling | MISSING | Standard feature | HIGH |
| PDF/Image export | MISSING | Standard feature | HIGH |
| Email alerts | MISSING | Standard feature | HIGH |
| Drill-down / drill-through | MISSING | Standard feature | HIGH |
| Pivot tables | MISSING | Standard feature | MEDIUM |
| User management / RBAC | MISSING | Standard feature | HIGH |
| Collaboration / sharing | MISSING | Standard feature | MEDIUM |
| Data transformations (ETL) | MISSING | dbt/Prep common | MEDIUM |
| Embedding (iframe) | MISSING | Standard feature | LOW |
| API access | MISSING | Standard feature | LOW |
| Version control (dashboards) | MISSING | Superset feature | LOW |
| Custom SQL editor | PARTIAL (query builder) | Full SQL IDE | MEDIUM |
| Caching layer | MISSING | Redis/memcache standard | MEDIUM |
| Mobile app | MISSING | Standard feature | LOW |
| Audit trail | MISSING | Standard for enterprise | MEDIUM |
| Data catalog | PARTIAL (schema explorer) | Full catalog (Alation-level) | MEDIUM |
| Semantic layer | PARTIAL (glossary) | Full semantic layer | MEDIUM |

### Gap Summary

- **Critical gaps (blockers for production):** No user auth/RBAC, no report scheduling, no export to PDF
- **High-value gaps:** Drill-down, more DB connectors, email alerts, caching
- **Nice-to-have:** Mobile, embedding, API, version control, full SQL editor

---

## 6. Technical Debt

### 6.1 Architecture Debt

| Item | Severity | Description |
|------|----------|-------------|
| ChatState monolith | HIGH | `chat.py` is ~590 lines orchestrating AI pipeline, chart building, process detection, streaming, insights, story — should be decomposed |
| SchemaState monolith | HIGH | `schema.py` is ~597 lines mixing schema, profiling, glossary, ERD — multiple concerns |
| No dependency injection | MEDIUM | AI pipeline components are tightly coupled; hard to test in isolation |
| Module-level process cache | MEDIUM | `ProcessDiscoveryCache` is module-level global — not testable, not multi-tenant |
| Cross-state complexity | MEDIUM | `async with self: other = await self.get_state(OtherState)` chains are fragile |
| Pickle serialization workaround | MEDIUM | `DBState.__getstate__()` override to exclude asyncpg.Pool is a workaround, not a solution |
| ChromaDB path coupling | LOW | Hard-coded `~/.biai/chromadb/` path — not configurable via settings |

### 6.2 Code Quality Debt

| Item | Severity | Description |
|------|----------|-------------|
| Inconsistent error handling | MEDIUM | Some errors are caught and logged, others propagate; no global error boundary |
| Magic strings in prompts | MEDIUM | LLM prompts embed assumptions about data (e.g., status column patterns) |
| Hardcoded confusable_pairs | LOW | `_generate_column_disambiguation()` has hardcoded table/column pairs specific to test data |
| No type-safe chart config | LOW | ECharts options are raw dicts — no schema validation |
| Duplicated chart building logic | MEDIUM | ECharts builder (~970 lines) and Plotly builder have overlapping responsibilities |

### 6.3 Testing Debt

| Item | Severity | Description |
|------|----------|-------------|
| No E2E tests | HIGH | No automated browser tests (Playwright/Selenium) |
| No integration tests with real Ollama | MEDIUM | AI pipeline tests mock LLM responses |
| Limited process discovery tests | MEDIUM | `test_process.py` is only in `biai/tests/` (non-standard location) |
| No load/stress tests | LOW | No performance benchmarks for concurrent queries |

### 6.4 Performance Concerns

| Item | Severity | Description |
|------|----------|-------------|
| Schema training on every connect | MEDIUM | Full Vanna re-training (DDL + docs + examples + discovery) per connection — can take 30-60s |
| ChromaDB re-initialization | LOW | Collections deleted and recreated on each training — expensive |
| No query result caching | MEDIUM | Identical queries re-execute against DB every time |
| InsightAgent ThreadPoolExecutor | LOW | 10s timeout per insight generation — blocks background task thread |
| ECharts builder string building | LOW | 970 lines of manual dict construction — could be templated |

### 6.5 Security Considerations

| Item | Severity | Description |
|------|----------|-------------|
| No authentication | CRITICAL | No user login — anyone with network access can query databases |
| Fernet key in .env | MEDIUM | Encryption key for connection passwords stored in plaintext .env file |
| No rate limiting | MEDIUM | No throttling on query execution or LLM calls |
| No query audit logging | MEDIUM | Executed SQL queries not logged for security audit |
| CORS not configured | LOW | Reflex default CORS — may be permissive |

---

## 7. Strengths Summary

1. **Full-stack Python** — Single language for frontend + backend + AI + DB is a strong DX choice
2. **Local AI inference** — No cloud LLM dependency, data stays on-premises
3. **RAG-based SQL generation** — ChromaDB + schema training improves query accuracy
4. **4-layer SQL security** — Defense-in-depth approach prevents SQL injection
5. **Self-correction loop** — Resilient to initial LLM errors (5 retries with feedback)
6. **Dialect abstraction** — Oracle and PostgreSQL handled transparently
7. **Dynamic process discovery** — Innovative feature for automatic business process mining
8. **Rich visualization stack** — ECharts (13 types) + Plotly fallback + React Flow processes
9. **Statistical insights** — Automated Pareto, anomaly, trend, correlation detection
10. **Data storytelling** — LLM-generated business narratives from query results
11. **Comprehensive data exploration** — Profiling, glossary, ERD in sidebar
12. **Solid test coverage** — 20 test files covering AI pipeline, SQL validation, and data processing

---

## 8. Recommendations

### Short-term (Quick Wins)

1. **Add authentication** — Even basic password protection (Reflex auth middleware)
2. **Persist chat history** — Save messages to disk/DB for session recovery
3. **Add query result caching** — Simple in-memory LRU cache for repeated queries
4. **Decompose ChatState** — Extract chart building, insight generation, story generation into separate modules
5. **Add E2E test suite** — Playwright tests for critical user flows

### Medium-term (Feature Parity)

1. **PDF/Image export** — Chart screenshots via puppeteer or matplotlib backend
2. **Report scheduling** — Background task scheduler (APScheduler or Celery)
3. **Drill-down capability** — Click chart elements to filter/zoom into data
4. **More DB connectors** — MySQL, SQLite, SQL Server (sqlglot supports all)
5. **Query audit logging** — Structured log of all executed queries with user, timestamp, results

### Long-term (Competitive Differentiation)

1. **Cloud LLM option** — OpenAI/Anthropic API alongside Ollama for better accuracy
2. **Semantic layer** — Full business metrics definitions beyond glossary
3. **Collaborative features** — Shared dashboards, team annotations
4. **Embedded analytics** — iframe/embed API for integration into other apps
5. **Mobile-responsive design** — Progressive Web App for mobile access

---

## Appendix A: File Size Distribution (Largest Files)

| File | Lines | Purpose |
|------|-------|---------|
| `ai/echarts_builder.py` | ~970 | ECharts option builder for 13 chart types |
| `state/schema.py` | ~597 | Schema explorer, profiling, glossary, ERD |
| `state/chat.py` | ~590 | Main chat orchestrator |
| `ai/pipeline.py` | ~542 | AI pipeline (training + processing) |
| `state/dashboard.py` | ~473 | Dashboard builder state |
| `state/query_builder.py` | ~446 | Visual SQL builder state |
| `ai/process_discovery.py` | ~400 | Dynamic process discovery engine |
| `state/process.py` | ~363 | Process flow visualization state |
| `ai/chart_advisor.py` | ~349 | Chart type recommendation |
| `db/dialect.py` | ~406 | Dialect rules, examples, disambiguation |

## Appendix B: Test Coverage Map

| Test File | Covers |
|-----------|--------|
| `test_sql_validator.py` | SQL validation (all 4 layers) |
| `test_self_correction.py` | Retry loop, refusal detection |
| `test_pipeline.py` | AIPipeline orchestration |
| `test_discovery.py` | Process discovery engine |
| `test_schema_manager.py` | Schema snapshot, table/column extraction |
| `test_query_executor.py` | Query execution, timeout, row limit |
| `test_dialect.py` | Dialect rules, examples, docs generation |
| `test_models.py` | Pydantic model validation |
| `test_ai_questions.py` | End-to-end question->SQL->result |
| `test_chart_advisor.py` | Chart type heuristics |
| `test_echarts_builder.py` | ECharts option construction |
| `test_business_glossary.py` | AI glossary generation |
| `test_data_profiler.py` | Column profiling, semantic types |
| `test_insight_agent.py` | Statistical insight generation |
| `test_analysis_planner.py` | Multi-step query decomposition |
| `test_process.py` | Process state management |
| `test_integration_db.py` | Integration with real databases |
| `test_integration_pipeline.py` | Full pipeline integration |

## Appendix C: Configuration Parameters

| Parameter | Default | Source |
|-----------|---------|--------|
| `OLLAMA_HOST` | `http://localhost:11434` | .env |
| `OLLAMA_MODEL` | `qwen3-coder:30b` | .env |
| `MAX_RETRIES` | 5 | constants.py |
| `QUERY_TIMEOUT` | 30s | constants.py |
| `ROW_LIMIT` | 10,000 | constants.py |
| `DISPLAY_ROW_LIMIT` | 100 | constants.py |
| `MAX_CHAT_HISTORY` | 100 | constants.py |
| `CHAT_PANEL_WIDTH` | 40% | constants.py |
| `DASHBOARD_PANEL_WIDTH` | 60% | constants.py |
| `DISCOVERY_MAX_TABLES` | 50 | constants.py |
| `DISCOVERY_MAX_CARDINALITY` | 30 | constants.py |
| `DISCOVERY_QUERY_TIMEOUT` | 10s | constants.py |
| `CHROMADB_PATH` | `~/.biai/chromadb/` | vanna_client.py |

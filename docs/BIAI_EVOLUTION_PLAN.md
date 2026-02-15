# BIAI Evolution Plan — From BI Chatbot to AI-First Analytics Platform

**Version:** 1.0
**Date:** 2026-02-14
**Based on:** BI Systems Research, LLM Models Research, BIAI Application Analysis
**Current codebase:** 15,358 LOC across ~90 Python files, 20 test files (3,104 LOC)

---

## 1. Executive Summary

### Vision for BIAI 2.0

BIAI evolves from a single-purpose NL-to-SQL chatbot into an **AI-first analytics platform** that combines conversational data exploration with autonomous insight generation — all running locally. Where today's BIAI answers the user's question, BIAI 2.0 also tells the user what questions they should be asking.

### Key Differentiators vs Existing BI Tools

1. **100% local-first architecture** — No cloud dependency for core functionality. Data never leaves the user's machine. Unlike Power BI Copilot, ThoughtSpot Spotter, or Supaboard, BIAI runs entirely on-premises with local LLM inference via Ollama.
2. **Zero-config intelligence** — No semantic models to build (Looker/LookML), no data prep required (Tableau Prep), no DAX formulas (Power BI). Point BIAI at a database and start asking questions.
3. **Process mining built-in** — Dynamic process discovery from ordinary database tables is unique among NL-to-SQL tools. No competitor (Vanna, Wren AI, BlazeSQL, Querio) offers this.
4. **Multi-model routing** — Intelligent routing between local and cloud LLMs based on query complexity. Simple queries stay free and local; complex queries can optionally use cloud APIs for higher accuracy.
5. **Full-stack Python** — Single-language codebase (Python + Reflex) makes the platform accessible to data teams without frontend expertise.

### Target User Persona

**Primary:** Data analyst or business user in a mid-size organization who needs to query Oracle/PostgreSQL databases without writing SQL. Comfortable with a desktop application. Values data privacy and local execution.

**Secondary:** IT/data team lead who wants to provide self-service analytics to business stakeholders without deploying a full BI stack (Tableau, Power BI).

### 5 Headline Features for BIAI 2.0

1. **Smart Model Router** — Automatic routing between local Qwen3-Coder:30b (free, fast) and cloud APIs (Claude Sonnet 4.5 for complex queries) with transparent cost tracking
2. **Interactive Dashboard with Cross-Filtering** — Click any chart element to filter all related widgets; KPI cards with sparklines; drill-down navigation
3. **AI Insight Agent** — Automatic anomaly detection, trend analysis, Pareto discovery, and follow-up question generation after every query
4. **Process Mining 2.0** — Sankey diagrams for state transitions, cycle time analysis, bottleneck detection, conformance checking
5. **Report Generator** — PDF export with charts, tables, and AI-generated narratives; scheduled report delivery

---

## 2. LLM Strategy

### 2.1 Primary Local Model

**Recommendation: Stay with Qwen3-Coder:30b (MoE, 3.3B active params)**

Justification from LLM research:
- Only 8 GB VRAM required (MoE architecture — 3.3B active out of 30B total)
- 256K context window — handles large schemas with dozens of tables
- ~50 t/s on RTX 4090, ~40 t/s on RTX 4070 Ti — well above the 15 t/s interactive threshold
- "Very Good" SQL accuracy rating, competitive with much larger dense models
- Already integrated and battle-tested in BIAI codebase (`biai/ai/vanna_client.py`)

No model change needed for Phase 1. The current model delivers excellent price/performance for the local use case.

### 2.2 Secondary/Fallback Local Model

**Recommendation: Add GPT-OSS-20B (OpenAI's open-weight MoE model)**

Justification:
- Available on Ollama (`ollama pull gpt-oss:20b`)
- 16 GB VRAM (fits RTX 4090, RTX 5090, or higher)
- "Very Good" SQL accuracy — potentially better than Qwen3-Coder:30b on certain query patterns
- ~60 t/s on RTX 4090 — faster than Qwen3-Coder
- OpenAI quality at zero cost

**Lightweight option for low-VRAM systems: Qwen3:8b (5 GB VRAM)**
- ~100 t/s on RTX 4060 Ti — ultra-fast for simple queries
- "Good" SQL accuracy — sufficient for straightforward SELECT queries
- Use as first-attempt model in multi-model routing

### 2.3 Cloud API Integration

**Tier 1 — Premium accuracy (complex queries):**
- **Claude Sonnet 4.5** — 94% accuracy on BIRD benchmark, $3.00/1M input tokens
- Use when: local model fails self-correction loop (>2 retries), multi-table JOINs, complex aggregations
- Prompt caching: 90% savings on repeated schema context (Anthropic feature)

**Tier 2 — Budget cloud (moderate queries):**
- **DeepSeek V3.2** — $0.028/1M input tokens (100x cheaper than Claude)
- Excellent SQL quality at negligible cost
- Use when: local model fails once but query is not highly complex

**Tier 3 — Ultra-fast cloud:**
- **Groq GPT-OSS-20B** — $0.075/1M input, ~900 TPS output
- Use when: user needs instant response and local inference is busy/slow

**Estimated monthly cost at medium usage (5,000 queries/month):**
- 80% local (free): $0
- 15% DeepSeek: $0.03
- 5% Claude Sonnet: $1.13
- **Total: ~$1.16/month** vs $22.50 if using Claude for everything

### 2.4 Multi-Model Routing Architecture

```
User Question
    |
    v
Complexity Classifier (rule-based + heuristic)
    |
    +-- Simple (single table, basic aggregation) --> Qwen3-Coder:30b (local)
    |
    +-- Medium (multi-table JOIN, subquery) --> GPT-OSS-20B (local) or DeepSeek API
    |
    +-- Complex (nested subqueries, window functions, CTEs) --> Claude Sonnet 4.5
    |
    v
Self-Correction Loop (up to 5 retries)
    |
    +-- If local model fails after 2 attempts --> escalate to next tier
    |
    v
Result
```

**Complexity classifier heuristics:**
- Count tables mentioned in question (schema context)
- Detect keywords: "compare", "trend", "over time", "top N by", "percentage"
- Count joins needed (from schema relationships)
- Historical accuracy for similar questions

**Implementation:** New file `biai/ai/model_router.py` with `ModelRouter` class. Integrates with `SelfCorrectionLoop` in `biai/ai/self_correction.py` to trigger escalation on repeated failures.

### 2.5 RAG Improvements for Vanna.ai

Current state: Vanna 1.x with ChromaDB + schema DDL + example queries + dialect documentation.

**Improvement 1: Semantic Layer (Business Glossary → Vanna Training)**
- Current `biai/ai/business_glossary.py` generates AI descriptions but they are NOT fed back into Vanna's training context
- Fix: After glossary generation, inject each `GlossaryEntry` as a documentation string into ChromaDB via `vanna.train(documentation=...)`
- This closes the loop: schema → glossary → Vanna context → better SQL

**Improvement 2: Query History as Training Data**
- Log successful queries (question → SQL → result row count) to `~/.biai/query_history.json`
- On next training, inject top 50 most-used queries as few-shot examples
- Implements the RAG feedback loop that Wren AI uses for accuracy improvement

**Improvement 3: Column Value Embeddings**
- Current categorical discovery (`get_categorical_columns`) runs DISTINCT queries but results are only used in prompts
- Embed actual column values (e.g., "status IN ('Active', 'Closed', 'Pending')") as ChromaDB documents
- When user asks "show me active orders", retrieval matches "Active" value → better WHERE clause

**Improvement 4: Evaluate Vanna 2.0 Migration**
- Vanna 2.0 offers agent-based framework, lifecycle hooks, user identity/RBAC, streaming UI
- Migration effort: Medium (breaking API changes from class methods to agent patterns)
- Timeline: Phase 3 (after core improvements stabilize)

### 2.6 Hardware Requirements

| Configuration | GPU | Models Supported | Use Case |
|--------------|-----|-----------------|----------|
| **Minimum** | RTX 4060 Ti 16GB | Qwen3-Coder:30b (8GB) | Single local model |
| **Recommended** | RTX 4090 24GB | Qwen3-Coder:30b + GPT-OSS-20B | Dual local models |
| **Power** | RTX 5090 32GB | Qwen3:32b dense (20GB) + smaller | Best local accuracy |
| **Budget** | RTX 3060 12GB | Qwen3:8b (5GB) | Basic queries only |
| **No GPU** | CPU only | Qwen3:8b Q4 (slow ~5 t/s) | Minimal, cloud recommended |

---

## 3. Presentation Layer — Dashboard & Visualization Overhaul

### 3.1 Dashboard Redesign

**Current state:** Fixed split-screen layout (sidebar 280px + chat 40% + dashboard 60%). Dashboard builder on separate `/dashboard` page. Basic `react-grid-layout` integration with 4 templates. No responsive design.

**Target:** Integrated, responsive dashboard with configurable grid that works alongside the chat panel.

#### 3.1.1 Responsive Grid Layout

Replace fixed percentage layout with a breakpoint-based system:

| Breakpoint | Layout | Sidebar | Chat | Dashboard |
|-----------|--------|---------|------|-----------|
| Desktop (>1400px) | Three-column | 280px | 40% | 60% |
| Laptop (1024-1400px) | Three-column | 240px collapsed | 40% | 60% |
| Tablet (768-1024px) | Two-column | Hidden (overlay) | 100% / toggle | 100% / toggle |
| Mobile (<768px) | Single column | Hidden (overlay) | 100% (tab switch) | 100% (tab switch) |

**Files to modify:**
- `biai/components/layout.py` — Add breakpoint detection and responsive flex layout
- `biai/config/constants.py` — Add breakpoint constants
- New: `biai/components/responsive.py` — Responsive wrapper utilities

#### 3.1.2 Widget Types to Add

Current widgets: chart, table, KPI card, text, insight, process flow.

New widgets based on BI research (Section 4 & 13):

| Widget | Description | Priority |
|--------|-------------|----------|
| **Sparkline KPI Card** | Current KPI card + embedded sparkline trend + period-over-period % change | HIGH |
| **Gauge Widget** | Target vs actual with progress arc (ECharts gauge exists, needs widget wrapper) | MEDIUM |
| **Filter/Slicer Widget** | Dropdown or date-range filter that cross-filters other widgets | HIGH |
| **Markdown/Text Widget** | Rich text annotation area with formatting | LOW |
| **Pivot Table Widget** | Cross-tab aggregation view | MEDIUM |
| **Map Widget** | Geographic data on Plotly choropleth/point map | LOW |
| **Metric Comparison** | Two metrics side-by-side with delta indicator | MEDIUM |

**Files to create/modify:**
- `biai/components/dashboard_builder/widget.py` — Add new widget types
- New: `biai/components/widgets/sparkline_kpi.py`
- New: `biai/components/widgets/gauge.py`
- New: `biai/components/widgets/filter_slicer.py`
- New: `biai/components/widgets/pivot_table.py`

#### 3.1.3 Drag-and-Drop Builder Improvements

- Pin any chat result directly to dashboard (current: basic pin exists via `PinnedState`)
- Widget resize handles with snap-to-grid (current: `react-grid-layout` already supports this)
- Widget configuration panel (click widget → sidebar shows config options)
- Dashboard auto-save with undo history
- Additional templates beyond current 4: Sales KPI, Operations Monitor, Financial Summary, Process Health

### 3.2 New Chart Types

**Current:** 13 ECharts types (bar, line, area, scatter, pie, gauge, funnel, heatmap, waterfall, treemap, sunburst, radar, parallel) + Plotly fallback.

**To add (ECharts — primary engine):**

| Chart Type | ECharts Support | Use Case | Complexity |
|-----------|----------------|----------|------------|
| **Sankey Diagram** | `type: 'sankey'` | Process flows, transition volumes | M |
| **Box Plot** | `type: 'boxplot'` | Statistical distribution | S |
| **Candlestick** | `type: 'candlestick'` | Financial time series | S |
| **Graph/Network** | `type: 'graph'` | Relationship visualization | M |
| **Calendar Heatmap** | `type: 'heatmap'` + calendar | Activity over time (GitHub-style) | M |
| **Polar/Rose** | Polar coordinate system | Cyclical data (hourly, seasonal) | S |

**To add (Plotly — for types ECharts lacks):**

| Chart Type | Plotly Support | Use Case | Complexity |
|-----------|---------------|----------|------------|
| **Violin Plot** | `go.Violin` | Distribution comparison | S |
| **Choropleth Map** | `go.Choropleth` | Geographic data | M |
| **Bubble Map** | `go.Scattergeo` | Location + magnitude | M |

**Files to modify:**
- `biai/ai/echarts_builder.py` — Add Sankey, box plot, candlestick, graph, calendar heatmap, polar builders
- `biai/ai/chart_builder.py` — Add violin, choropleth, bubble map builders
- `biai/models/chart.py` — Add new `ChartType` enum values
- `biai/ai/chart_advisor.py` — Update heuristics for new chart types

#### Interactive Features (Cross-Filtering & Drill-Down)

**Cross-filtering** (BI Research Section 14 — identified as major gap):
- Click on a bar/pie segment → emit event with clicked dimension value
- All other widgets on the same dashboard filter to that value
- Visual indicator showing active filter + "Reset Filters" button

**Drill-down** (hierarchical):
- Date: Year → Quarter → Month → Week → Day
- Geography: Country → Region → City
- Category: Department → Team → Individual
- Click a chart element → zoom into next hierarchy level
- Breadcrumb trail showing current drill path

**Implementation:**
- New: `biai/state/filter.py` — `FilterState` managing cross-filter context
- Modify: `biai/components/dashboard_builder/widget.py` — Add `on_filter` event handlers
- Modify: `biai/state/dashboard.py` — Propagate filters across widgets
- Modify: `biai/ai/echarts_builder.py` — Add click event handlers to ECharts options

### 3.3 Process Flow Visualization Upgrades

**Current:** React Flow with custom node types, token animation, layout toggle, edit mode, comparison view.

#### 3.3.1 Sankey Diagrams for Transitions

Convert `ProcessState` transition data into Sankey diagram format:
- **Nodes** = process states (e.g., "New", "In Progress", "Closed")
- **Links** = transitions with volume (case count) determining width
- **Color** = transition time (green = fast, red = slow)
- Use ECharts Sankey (`type: 'sankey'`) for rendering

**Files:**
- New: `biai/ai/process_sankey_builder.py` — Converts ProcessFlow → ECharts Sankey option
- Modify: `biai/components/process_map_card.py` — Toggle between React Flow and Sankey view

#### 3.3.2 BPMN-Style Process Maps

Enhance React Flow diagrams with BPMN notation:
- Start event (circle), End event (bold circle)
- Activity nodes (rounded rectangles — current)
- Gateway nodes (diamonds) for decision points
- Swimlanes per actor/department (using React Flow groups)

**Libraries:** `@liangfaan/reactflow-swimlane` for swimlane support (BI Research Section 6.3).

**Files:**
- New: `biai/components/react_flow/bpmn_nodes.py` — BPMN-style custom node components
- Modify: `biai/ai/process_layout.py` — Add swimlane layout calculation

#### 3.3.3 Timeline/Gantt Views

For processes with timestamp data:
- Horizontal timeline showing process instances
- Color-coded bars per status/phase
- Duration markers
- Deadline indicators

Use ECharts custom series or Plotly `go.Bar(orientation='h')` with timeline layout.

#### 3.3.4 Swimlane Diagrams

Group process nodes by responsible actor/department:
- Detect actor columns in schema (e.g., `assigned_to`, `department`, `handler`)
- Create horizontal swimlanes with process steps distributed across lanes
- Show handoff points between lanes

### 3.4 KPI & Scorecard System

**Current:** Basic KPI card for single-row queries with <= 4 columns (`biai/components/kpi_card.py`).

#### 3.4.1 Enhanced KPI Card

Upgrade to include (BI Research Section 13):
- **Large metric value** (primary visual focus)
- **Metric label** with optional icon
- **Period-over-period change** (%, absolute) with color coding (green up, red down)
- **Sparkline** (last 7/30/90 days trend line)
- **Target indicator** (% of target achieved)
- **Trend arrow** (up/down/flat)

**Implementation:**
- Modify: `biai/components/kpi_card.py` — Complete redesign with sparkline and comparison
- New: `biai/ai/kpi_analyzer.py` — Detect KPI-worthy metrics and calculate trends
- The sparkline can use a minimal ECharts instance or SVG path

#### 3.4.2 Scorecard Dashboard Template

Pre-configured dashboard layout:
- Top row: 4-6 KPI cards (hero section)
- Middle: Primary chart (line/bar with trend)
- Bottom: Data table with details
- Right sidebar: Top/Bottom 5 lists

#### 3.4.3 Metric Tracking Over Time

- Define metric queries (e.g., "total revenue this month")
- Schedule re-execution at intervals (hourly, daily)
- Store historical values in `~/.biai/metrics/`
- Display sparkline from historical data
- Alert when threshold is crossed (UI notification)

### 3.5 Report Generation

**Current:** CSV export only (BI Research Section 10 — identified as major gap).

#### 3.5.1 PDF Export

Generate PDF reports containing:
- Dashboard screenshot (all visible charts + tables)
- AI-generated narrative summary
- Data tables with formatting
- Company header/footer with logo

**Technical approach:**
- Use `weasyprint` (Python HTML-to-PDF) or `reportlab`
- Render dashboard to HTML template → convert to PDF
- ECharts charts: Use `echarts.getDataURL()` to get PNG → embed in PDF
- Alternative: Server-side rendering with Playwright for pixel-perfect screenshots

**Files:**
- New: `biai/utils/pdf_export.py` — PDF generation pipeline
- New: `biai/templates/report.html` — HTML template for PDF rendering
- Modify: `biai/state/query.py` — Add `export_pdf` event handler

#### 3.5.2 Excel Export

Beyond current CSV:
- Multiple sheets (data, summary, charts as images)
- Formatted headers, auto-column-width
- Use `openpyxl` library

**Files:**
- New: `biai/utils/excel_export.py` — Excel generation with formatting
- Modify: `biai/state/query.py` — Add `export_xlsx` event handler

#### 3.5.3 Scheduled Reports

- Define report = dashboard template + query + schedule (cron expression)
- Background scheduler executes queries and generates PDF
- Save to configured directory or send via email (SMTP)
- Use `APScheduler` for scheduling

**Files:**
- New: `biai/utils/report_scheduler.py` — APScheduler integration
- New: `biai/models/report.py` — Report definition model
- New: `biai/state/report.py` — ReportState for UI management

#### 3.5.4 Report Templates

Pre-built report layouts:
- Executive Summary (KPIs + key charts + AI narrative)
- Detailed Analysis (full data tables + charts + insights)
- Process Health Report (process flows + metrics + bottlenecks)
- Custom (user-defined layout)

---

## 4. Dynamic Analytics Engine (AI-Powered)

### 4.1 AI Insights Generator

**Current:** `InsightAgent` in `biai/ai/insight_agent.py` generates Pareto, anomaly (z-score), trend, correlation, and distribution skew insights. Runs in ThreadPoolExecutor with 10s timeout.

#### 4.1.1 Anomaly Detection Improvements

Current: Z-score based (>2 std deviations). Add:
- **IQR method** — More robust to non-normal distributions
- **Seasonal decomposition** — Detect anomalies relative to seasonal pattern (STL decomposition)
- **Contextual anomalies** — "This month's revenue is normal overall but unusual for Q1"
- **Multi-variate** — Detect unusual combinations (high quantity + low revenue = possible discount abuse)

**Files to modify:** `biai/ai/insight_agent.py` — Add new anomaly detection methods

#### 4.1.2 Trend Analysis Enhancements

Current: Linear regression trend line. Add:
- **Moving average** (7-day, 30-day) with configurable window
- **Year-over-year comparison** — Automatic when date column detected
- **Acceleration/deceleration detection** — "Revenue growth is slowing: +15% last month vs +8% this month"
- **Breakpoint detection** — Identify dates where trend changes direction

#### 4.1.3 Pareto Analysis (Current — Enhance)

Current: 80/20 rule identification. Add:
- **Multi-level Pareto** — "Top 5 customers account for 60% of revenue; their top 3 products account for 80% of their orders"
- **Interactive drill** — Click a Pareto segment to see breakdown

#### 4.1.4 Correlation Discovery

Current: Pearson correlation between numeric columns. Add:
- **Spearman rank correlation** — For non-linear relationships
- **Categorical correlation** (Cramér's V) — Between categorical columns
- **Correlation explanation** — "Orders and revenue have strong positive correlation (r=0.92), which is expected"
- **Unexpected correlations** — Highlight surprising relationships

### 4.2 Smart Suggestions

**Current:** Pattern-based follow-up suggestions in `ChatState` (hardcoded patterns like "Show trend over time", "Group by {column}").

#### 4.2.1 Context-Aware Follow-Up Questions

After each query result, generate 3-5 follow-up questions based on:
- **Data shape** — If result has time column: "Show trend over last 12 months"
- **Insight findings** — If anomaly detected: "What changed in {anomaly_period}?"
- **Schema relationships** — If FK exists: "Break down by {related_table}"
- **Statistical properties** — If skewed distribution: "What are the top 10 outliers?"
- **Previous conversation** — If user asked about revenue: "How does this compare to costs?"

**Implementation:**
- Modify: `biai/ai/pipeline.py` — After insights, generate context-aware suggestions
- New: `biai/ai/suggestion_engine.py` — `SuggestionEngine` class
- Use LLM to generate natural-language questions from data context + schema + insights

#### 4.2.2 Schema-Aware Question Generation

On database connection (after schema training):
- Generate 10-20 "starter questions" based on tables and columns
- Display in chat panel as clickable chips
- Example: Schema has `orders(id, customer_id, total, status, created_at)` → suggest "What's the total revenue by month?", "Which customers have the most orders?", "What's the order status distribution?"

**Files:**
- New: `biai/ai/question_generator.py` — Generate questions from schema
- Modify: `biai/state/chat.py` — Display starter questions after connection

### 4.3 Data Storytelling

**Current:** `DataStoryteller` in `biai/ai/storyteller.py` generates narratives with context, findings, implications, recommendations. Activated by `story_mode` toggle.

#### 4.3.1 Narrative Generation from Multi-Step Analysis

When `AnalysisPlanner` decomposes a complex question into multiple steps:
- Generate a coherent narrative that connects all step results
- Structure: Introduction → Key Findings → Supporting Data → Implications → Recommendations
- Include inline references to specific data points

#### 4.3.2 Executive Summary Generation

One-click "Generate Executive Summary" for current dashboard:
- Aggregate all visible widget data
- Generate 3-5 bullet point summary
- Include most important KPI changes and anomalies
- Format for email or presentation

#### 4.3.3 Automated Reporting Narratives

For scheduled reports (Section 3.5):
- Auto-generate narrative section comparing current period vs previous
- Highlight notable changes, anomalies, and trend shifts
- Natural language, not just numbers

### 4.4 Predictive Analytics

#### 4.4.1 Time Series Forecasting

When data has a time column with sufficient history (>12 data points):
- **Simple forecast** — Linear extrapolation (already possible with trend line)
- **Statistical forecast** — Exponential smoothing (Holt-Winters) via `statsmodels`
- **Confidence interval** — Show prediction range (80%, 95%)
- Display as dashed continuation of actual data line

**Implementation:**
- New: `biai/ai/forecaster.py` — `Forecaster` class using statsmodels
- Modify: `biai/ai/echarts_builder.py` — Add forecast series rendering (dashed line + confidence band)
- Modify: `biai/ai/chart_advisor.py` — Detect forecast opportunity and suggest

#### 4.4.2 What-If Analysis

Allow users to ask "What if revenue grows 10% per month?":
- Parse the scenario from natural language
- Apply transformation to current data
- Show original vs projected side-by-side
- Use LLM to generate the transformation logic

#### 4.4.3 Scenario Comparison

Compare multiple scenarios on the same chart:
- "Compare optimistic (15% growth) vs pessimistic (5% growth) vs actual"
- Overlay multiple forecast lines with different parameters
- Interactive legend to toggle scenarios

### 4.5 Conversational Analytics

**Current:** Multi-turn conversation with last 5 exchanges as context. Follow-up suggestions.

#### 4.5.1 Multi-Turn Conversation Improvements

- **Extend context window** from 5 to 10 exchanges (Qwen3-Coder:30b has 256K context)
- **Reference previous results** — "Filter that by status = Active" (resolve "that" to last query)
- **Pronoun resolution** — "How many of them are overdue?" → resolve "them" to previous result set
- **Implicit context** — After querying orders table, "show me the customers" → infer JOIN to customers table

**Files to modify:**
- `biai/state/chat.py` — Enhance conversation context building
- `biai/ai/pipeline.py` — Pass richer context to Vanna including previous SQL and results summary

#### 4.5.2 Natural Language Commands

Support conversational commands on existing results:
- "Drill into that" → drill-down on last chart
- "Filter by X" → apply filter to current dashboard
- "Compare with last month" → re-run query with date offset
- "Export this as PDF" → trigger PDF export
- "Pin this to dashboard" → pin current result
- "Sort by revenue descending" → re-sort current table

**Implementation:**
- New: `biai/ai/command_parser.py` — Parse intent (query vs command) from user input
- Modify: `biai/state/chat.py` — Route commands to appropriate handlers

---

## 5. Process Mining 2.0

### 5.1 Advanced Discovery

**Current:** `ProcessDiscoveryEngine` (`biai/ai/process_discovery.py`, ~400 lines) discovers processes from status columns, transition tables, and FK chains. Cached in module-level `ProcessDiscoveryCache`.

#### 5.1.1 Event Log Reconstruction from Regular Tables

Most databases don't have explicit event logs. BIAI should reconstruct them:
- Detect `created_at`, `updated_at`, `status_changed_at` timestamp columns
- Detect audit/history tables (e.g., `order_history`, `status_log`, `audit_trail`)
- Reconstruct event sequence: (case_id, activity, timestamp, resource)
- Support both explicit event logs and implicit reconstruction

**Files:**
- New: `biai/ai/event_log_builder.py` — Reconstruct event logs from database tables
- Modify: `biai/ai/process_discovery.py` — Use event log builder as input

#### 5.1.2 Conformance Checking

Compare discovered process against expected/ideal process:
- User defines "happy path" (or BIAI discovers the most common path)
- Highlight deviations: skipped steps, repeated steps, out-of-order steps
- Calculate conformance rate (% of cases following happy path)
- Visualize deviations with color coding on process map

**Files:**
- New: `biai/ai/conformance_checker.py` — Conformance checking algorithms
- Modify: `biai/components/react_flow/process_flow.py` — Add deviation highlighting

#### 5.1.3 Variant Analysis

Discover and compare process variants:
- Group cases by execution path (sequence of activities)
- Rank variants by frequency
- Show top 5 variants side-by-side
- Highlight differences between variants

**Files:**
- New: `biai/ai/variant_analyzer.py` — Process variant discovery and comparison
- Modify: `biai/components/react_flow/process_comparison.py` — Multi-variant comparison view

### 5.2 Rich Visualizations

#### 5.2.1 Sankey Diagram for State Transitions with Volume

Transform transition data into Sankey:
- Node width proportional to case count entering that state
- Link width proportional to transition volume
- Color gradient from source to target node color
- Interactive: hover shows transition count and percentage

**ECharts Sankey implementation:**
```python
# In new biai/ai/process_sankey_builder.py
option = {
    "series": [{
        "type": "sankey",
        "data": [{"name": state} for state in states],
        "links": [
            {"source": from_state, "target": to_state, "value": count}
            for from_state, to_state, count in transitions
        ],
        "emphasis": {"focus": "adjacency"},
        "lineStyle": {"color": "gradient", "curveness": 0.5}
    }]
}
```

#### 5.2.2 Dotted Chart / Event Log Visualization

Scatter plot where:
- X-axis = timestamp
- Y-axis = case ID (one row per case)
- Dots = events, colored by activity type
- Shows parallelism, batch patterns, delays

Use ECharts scatter with category Y-axis.

#### 5.2.3 Social Network Analysis

When resource/actor data is available:
- Build handoff graph: who passes work to whom
- Node size = workload (case count)
- Edge width = handoff frequency
- Identify bottleneck actors (high degree centrality)
- Use ECharts graph type

### 5.3 Process Metrics

#### 5.3.1 Cycle Time Analysis

For each process:
- **Average cycle time** (start to end)
- **Median cycle time** (less sensitive to outliers)
- **Per-activity duration** breakdown
- **Waiting time** vs **processing time** split
- **Cycle time distribution** (histogram)

**Implementation:**
- New: `biai/ai/process_metrics.py` — `ProcessMetricsCalculator` class
- Requires event log with timestamps per activity

#### 5.3.2 Bottleneck Detection with Quantification

- Identify activity with longest average duration
- Identify transition with longest average wait time
- Quantify impact: "Approval step adds average 3.2 days, affecting 78% of cases"
- Color-code process map nodes by duration (heatmap overlay)

#### 5.3.3 Rework Rate Calculation

- Count cases where same activity is executed more than once
- Calculate rework rate per activity
- Visualize loops on process map with loop count
- Identify root causes of rework (which upstream activities lead to rework)

#### 5.3.4 SLA Compliance Tracking

- Define SLA thresholds per activity (e.g., "Approval must complete within 24 hours")
- Calculate compliance rate
- Highlight SLA violations on process map
- Trend chart: SLA compliance over time

---

## 6. UX/UI Modernization

### 6.1 Design System

**Current:** Dark theme with Tailwind CSS, violet accent, default Plotly/ECharts colors.

#### 6.1.1 Color Palette

Define BIAI-specific design tokens (BI Research Section 15):

**Primary palette:**
- Background: `#0f0f23` (deep navy) — current dark theme base
- Surface: `#1a1a3e` (elevated surfaces)
- Border: `#2d2d5e` (subtle borders)
- Accent: `#8b5cf6` (violet — current)
- Accent hover: `#a78bfa`

**Data visualization palette (8 colors — categorical):**
Accessible, distinguishable for color blindness:
```
#6366f1 (indigo), #06b6d4 (cyan), #f59e0b (amber), #10b981 (emerald),
#ef4444 (red), #8b5cf6 (violet), #f97316 (orange), #64748b (slate)
```

**Semantic palette:**
- Success: `#22c55e` (green)
- Warning: `#f59e0b` (amber)
- Error: `#ef4444` (red)
- Info: `#3b82f6` (blue)

**Sequential palette (for heatmaps, choropleth):**
- Light: `#dbeafe` → Dark: `#1e3a8a` (blue gradient)

**Files:**
- New: `biai/config/design_tokens.py` — All color, spacing, typography tokens
- Modify: `biai/ai/echarts_builder.py` — Use design tokens for chart colors
- Modify: `biai/ai/dynamic_styler.py` — Apply token-based styling

#### 6.1.2 Typography

- **Headers:** Inter or Geist Sans (modern, clean)
- **Body:** Same family, regular weight
- **Code/SQL:** JetBrains Mono or Fira Code
- **Metrics/KPIs:** Tabular numerals (fixed-width digits for alignment)

#### 6.1.3 Spacing System

8px base grid:
- `xs`: 4px, `sm`: 8px, `md`: 16px, `lg`: 24px, `xl`: 32px, `2xl`: 48px

#### 6.1.4 Component Library Standardization

Ensure all components follow consistent patterns:
- Button sizes: sm, md, lg
- Input field styling: consistent border, focus ring, error state
- Card component: consistent padding, border radius, shadow
- Loading states: consistent skeleton/spinner patterns

### 6.2 Navigation & Layout

#### 6.2.1 Responsive Design

(Detailed in Section 3.1.1 above — breakpoint-based layout)

#### 6.2.2 Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` / `Cmd+K` | Command palette (search everything) |
| `Ctrl+Enter` | Send message |
| `Ctrl+Shift+S` | Toggle sidebar |
| `Ctrl+E` | Focus chat input |
| `Ctrl+D` | Toggle dashboard view |
| `Escape` | Close modal/dialog/fullscreen |
| `Ctrl+Shift+C` | Copy current SQL |
| `Ctrl+Shift+X` | Export CSV |

**Implementation:**
- New: `biai/components/keyboard_shortcuts.py` — Global keyboard handler
- Use Reflex `rx.script` with JavaScript keyboard event listeners

#### 6.2.3 Command Palette (Ctrl+K)

Searchable command palette for quick access:
- Recent queries
- Saved queries
- Navigation (pages, settings)
- Actions (export, pin, fullscreen)
- Schema search (find table/column)

**Implementation:**
- New: `biai/components/command_palette.py` — Modal with search input
- New: `biai/state/command.py` — CommandState managing search and actions

### 6.3 User Productivity

#### 6.3.1 Query History with Search

**Current:** Chat messages in `ChatState.messages` (list), lost on refresh.

Improvements:
- Persist all queries to `~/.biai/history.json` with timestamp, question, SQL, row count
- Searchable history panel in sidebar
- Click to re-run any historical query
- Filter by date range, table, keyword

**Files:**
- New: `biai/utils/history_storage.py` — Query history persistence
- New: `biai/state/history.py` — HistoryState for UI
- New: `biai/components/history_panel.py` — History sidebar component

#### 6.3.2 Favorites/Bookmarks

**Current:** `SavedQueriesState` exists with basic save/load.

Enhance:
- Categorize saved queries into folders
- Add descriptions/tags
- Quick-access toolbar for top 5 favorites
- Share saved queries (export/import JSON)

#### 6.3.3 Query Templates Library

Pre-built query templates per domain:
- Sales: Revenue by period, Top customers, Product mix
- HR: Headcount trends, Turnover rate, Department distribution
- Finance: Cost breakdown, Budget vs Actual, Cash flow
- Operations: Order fulfillment, SLA compliance, Inventory levels

**Files:**
- New: `biai/config/query_templates.py` — Template definitions
- Modify: `biai/components/chat_panel.py` — Template picker UI

#### 6.3.4 Natural Language Result Filtering

After viewing a result table:
- Type natural language filter in a filter bar above the table
- Examples: "only active customers", "revenue > 10000", "last 30 days"
- Translates to client-side DataFrame filter (no DB re-query)

### 6.4 Collaboration (Future — Phase 4)

#### 6.4.1 Share Dashboard via URL

- Generate shareable URL for any dashboard state
- Encode dashboard config + filter state in URL parameters
- Recipient opens BIAI, sees same dashboard (requires same DB access)

#### 6.4.2 Comments/Annotations on Charts

- Click a data point → add text annotation
- Annotations persist and display to other viewers
- Support @mentions (if user management exists)

#### 6.4.3 Team Workspaces

- Multiple users with shared dashboards, saved queries, query templates
- Role-based access: Admin, Analyst, Viewer
- Requires authentication system (Section 10 — Risk Assessment)

---

## 7. Architecture Evolution

### 7.1 Multi-Model LLM Support

**Current:** Single Ollama model configured in `ModelState` (`biai/state/model.py`).

#### 7.1.1 Model Configuration System

```python
# New: biai/config/model_config.py
@dataclass
class ModelConfig:
    name: str           # Display name
    provider: str       # "ollama", "groq", "anthropic", "deepseek"
    model_id: str       # e.g., "qwen3-coder:30b", "claude-sonnet-4-5"
    api_key: str | None # For cloud providers
    base_url: str       # API endpoint
    max_tokens: int
    temperature: float
    cost_per_1k_input: float   # For cost tracking
    cost_per_1k_output: float
    tier: str           # "local", "budget_cloud", "premium_cloud"
```

#### 7.1.2 Automatic Model Selection Based on Query Complexity

(Detailed in Section 2.4 — Multi-Model Routing Architecture)

**Complexity scoring heuristics:**
- 1 table, no aggregation → Simple (score 1-3)
- 2-3 tables, basic JOIN, GROUP BY → Medium (score 4-6)
- 4+ tables, subqueries, window functions, CTEs → Complex (score 7-10)

#### 7.1.3 Fallback Chain

```
Local Primary (Qwen3-Coder:30b)
    → fails 2x → Local Secondary (GPT-OSS-20B)
        → fails 2x → Cloud Budget (DeepSeek V3.2)
            → fails 2x → Cloud Premium (Claude Sonnet 4.5)
                → fails → Return error to user
```

Total retries across chain: up to 8 attempts (vs current 5 on single model).

### 7.2 Plugin System

#### 7.2.1 Custom Chart Types as Plugins

Allow adding new visualization types without modifying core code:

```python
# Plugin interface
class ChartPlugin(ABC):
    @property
    def chart_type(self) -> str: ...
    @property
    def description(self) -> str: ...
    def can_render(self, df: pd.DataFrame, config: ChartConfig) -> bool: ...
    def build_option(self, df: pd.DataFrame, config: ChartConfig) -> dict: ...
```

**Plugin discovery:** Scan `~/.biai/plugins/charts/` for Python modules implementing `ChartPlugin`.

#### 7.2.2 Custom Data Connectors

Similar plugin interface for database connectors:

```python
class ConnectorPlugin(ABC):
    @property
    def db_type(self) -> str: ...
    async def connect(self, config: ConnectionConfig) -> None: ...
    async def execute(self, sql: str) -> QueryResult: ...
    async def get_schema_snapshot(self, schema: str) -> SchemaSnapshot: ...
```

Enable community-contributed connectors for MySQL, SQLite, SQL Server, ClickHouse, DuckDB.

#### 7.2.3 Custom AI Processors

Plugins for custom insight types:
- Domain-specific anomaly detection
- Industry-specific KPI calculations
- Custom report generators

### 7.3 Performance

#### 7.3.1 Query Result Caching

**Current:** No caching — identical queries re-execute against DB every time.

Implementation:
- **In-memory LRU cache** (`functools.lru_cache` or `cachetools.TTLCache`)
- Cache key: `hash(sql + connection_config)`
- TTL: Configurable (default 5 minutes)
- Maximum cache entries: 100
- Cache invalidation: On schema change, manual clear, or TTL expiry
- Display "Cached" badge on results from cache

**Files:**
- New: `biai/utils/query_cache.py` — `QueryCache` class with TTL and LRU eviction
- Modify: `biai/db/query_executor.py` — Check cache before executing
- Modify: `biai/state/query.py` — Show cache indicator

#### 7.3.2 Incremental Schema Updates

**Current:** Full Vanna re-training (DDL + docs + examples + discovery) on every connection (~30-60s).

Improvement:
- Cache schema snapshot to disk (`~/.biai/schema_cache/{connection_hash}.json`)
- On reconnect, compare cached schema with current
- Only re-train changed tables/columns
- Full re-train only if >20% of schema changed

**Files:**
- New: `biai/utils/schema_cache.py` — Schema snapshot persistence and diff
- Modify: `biai/ai/training.py` — Incremental training support

#### 7.3.3 WebSocket for Real-Time Updates

**Current:** Reflex already uses WebSocket for state synchronization.

Improvements:
- Stream query execution progress (parsing → validating → executing → rendering)
- Stream chart rendering (show skeleton → populate data progressively)
- Real-time dashboard refresh with configurable interval

### 7.4 API Layer

#### 7.4.1 REST API for Embedded Analytics

Expose BIAI capabilities via REST API for integration:

```
POST /api/query     — Submit NL question, return SQL + results
POST /api/sql       — Execute SQL directly, return results
GET  /api/schema    — Get database schema
GET  /api/charts    — Get chart configurations
POST /api/export    — Generate PDF/Excel export
```

**Implementation:** Reflex supports custom API routes. Add API endpoints alongside existing pages.

**Files:**
- New: `biai/api/routes.py` — FastAPI-style route definitions
- New: `biai/api/auth.py` — API key authentication
- New: `biai/api/serializers.py` — Response serialization

#### 7.4.2 Webhook Support for Alerts

When metric thresholds are crossed or anomalies detected:
- Send webhook POST to configured URL
- Payload: metric name, current value, threshold, timestamp
- Support Slack, Teams, email, custom URL

#### 7.4.3 Integration with External Tools

- **Slack bot** — Ask BIAI questions from Slack
- **CLI tool** — Command-line interface for batch queries
- **Jupyter integration** — `from biai import ask; ask("total revenue")` in notebooks

---

## 8. Implementation Roadmap

### Phase 1: Quick Wins (1-2 weeks)

| # | Item | Description | Files to Modify | Complexity | Business Value |
|---|------|-------------|----------------|-----------|----------------|
| 1.1 | **Add GPT-OSS-20B model option** | Add to Ollama model list, allow switching in UI | `biai/state/model.py`, `biai/components/model_selector.py` | S | Users with 16GB+ VRAM get better accuracy |
| 1.2 | **Design tokens file** | Centralize all colors, spacing, typography constants | New: `biai/config/design_tokens.py`, modify ECharts builder | S | Consistent visual identity across all charts |
| 1.3 | **Enhanced KPI cards** | Add trend arrow, period-over-period %, sparkline to existing KPI component | `biai/components/kpi_card.py`, `biai/state/query.py` | S | KPI cards become genuinely useful (vs current bare numbers) |
| 1.4 | **Query result caching** | In-memory TTL cache for repeated queries | New: `biai/utils/query_cache.py`, modify `biai/db/query_executor.py` | S | Instant response for repeated queries |
| 1.5 | **Keyboard shortcuts** | Ctrl+K (command palette stub), Ctrl+Enter (send), Escape (close) | New: `biai/components/keyboard_shortcuts.py` | S | Power user productivity |
| 1.6 | **Persistent query history** | Save queries to disk, searchable in sidebar | New: `biai/utils/history_storage.py`, new: `biai/components/history_panel.py` | S | Session recovery, learning from past queries |
| 1.7 | **Loading skeletons** | Differentiated skeleton screens for chat, chart, table, KPI | Modify: `biai/components/chat_panel.py`, `biai/components/dashboard_panel.py` | S | Better perceived performance |
| 1.8 | **Sankey chart type** | Add ECharts Sankey for flow data (process transitions) | `biai/ai/echarts_builder.py`, `biai/models/chart.py`, `biai/ai/chart_advisor.py` | S | Direct process transition visualization |

### Phase 2: Core Improvements (2-4 weeks)

| # | Item | Description | Technical Approach | Complexity | Dependencies |
|---|------|-------------|-------------------|-----------|--------------|
| 2.1 | **Cross-filtering** | Click chart element → filter all dashboard widgets | New `FilterState`, modify widget event handlers, ECharts click events | M | 1.2 (design tokens for filter indicators) |
| 2.2 | **Multi-model routing** | Complexity classifier + model router with escalation | New: `biai/ai/model_router.py`, modify `biai/ai/self_correction.py` | M | 1.1 (GPT-OSS model available) |
| 2.3 | **Cloud API integration** | Add Groq, DeepSeek, Anthropic API support alongside Ollama | New: `biai/ai/cloud_providers.py`, modify `biai/ai/vanna_client.py` | M | 2.2 (model router uses cloud as fallback) |
| 2.4 | **PDF export** | Generate PDF reports with charts + tables + AI narrative | New: `biai/utils/pdf_export.py`, use weasyprint or reportlab | M | None |
| 2.5 | **Excel export** | Formatted .xlsx with multiple sheets | New: `biai/utils/excel_export.py`, use openpyxl | S | None |
| 2.6 | **Context-aware suggestions** | AI-generated follow-up questions based on results + schema + insights | New: `biai/ai/suggestion_engine.py`, modify `biai/state/chat.py` | M | None |
| 2.7 | **Schema-aware starter questions** | Generate clickable question chips on DB connection | New: `biai/ai/question_generator.py`, modify `biai/components/chat_panel.py` | M | None |
| 2.8 | **Drill-down navigation** | Hierarchical drill (Year→Month→Day) on time-series charts | Modify `biai/ai/echarts_builder.py`, new: `biai/state/drill.py` | M | 2.1 (cross-filtering infrastructure) |
| 2.9 | **RAG feedback loop** | Inject successful query history + glossary into Vanna training | Modify `biai/ai/training.py`, new: `biai/utils/history_storage.py` | M | 1.6 (query history) |
| 2.10 | **Incremental schema training** | Cache schema, diff on reconnect, train only changes | New: `biai/utils/schema_cache.py`, modify `biai/ai/training.py` | M | None |
| 2.11 | **Box plot + Candlestick charts** | Add ECharts box plot and candlestick chart types | `biai/ai/echarts_builder.py`, `biai/models/chart.py` | S | None |
| 2.12 | **Responsive layout** | Breakpoint-based layout (desktop/laptop/tablet) | `biai/components/layout.py`, new: `biai/components/responsive.py` | M | None |

### Phase 3: Advanced Features (4-8 weeks)

| # | Item | Description | Technical Approach | Complexity | Dependencies |
|---|------|-------------|-------------------|-----------|--------------|
| 3.1 | **Process Sankey diagrams** | Convert process flows to Sankey with volume + duration coloring | New: `biai/ai/process_sankey_builder.py`, modify `biai/components/process_map_card.py` | M | 1.8 (Sankey chart type) |
| 3.2 | **Event log reconstruction** | Build event logs from audit/history tables for process mining | New: `biai/ai/event_log_builder.py`, modify `biai/ai/process_discovery.py` | L | None |
| 3.3 | **Cycle time + bottleneck analysis** | Calculate and visualize process metrics | New: `biai/ai/process_metrics.py`, modify process visualization | L | 3.2 (event log) |
| 3.4 | **Time series forecasting** | Holt-Winters forecast with confidence bands | New: `biai/ai/forecaster.py`, modify `biai/ai/echarts_builder.py` | M | None |
| 3.5 | **Command palette** | Ctrl+K searchable command interface | New: `biai/components/command_palette.py`, `biai/state/command.py` | M | 1.5 (keyboard shortcuts) |
| 3.6 | **Conversational commands** | "Filter by X", "Drill into that", "Compare with last month" | New: `biai/ai/command_parser.py`, modify `biai/state/chat.py` | L | 2.1 (cross-filtering), 2.8 (drill-down) |
| 3.7 | **Conformance checking** | Compare actual process vs happy path, highlight deviations | New: `biai/ai/conformance_checker.py`, modify process flow component | L | 3.2 (event log) |
| 3.8 | **Variant analysis** | Discover and compare process execution paths | New: `biai/ai/variant_analyzer.py`, modify comparison view | L | 3.2 (event log) |
| 3.9 | **Pivot table widget** | Cross-tab aggregation view in dashboard | New: `biai/components/widgets/pivot_table.py` | M | None |
| 3.10 | **Vanna 2.0 evaluation** | Evaluate migration from Vanna 1.x to agent-based Vanna 2.0 | Modify `biai/ai/vanna_client.py` (experimental branch) | L | None |
| 3.11 | **Enhanced anomaly detection** | IQR, seasonal decomposition, contextual anomalies | Modify `biai/ai/insight_agent.py` | M | None |
| 3.12 | **Report scheduling** | APScheduler-based periodic report generation | New: `biai/utils/report_scheduler.py`, `biai/models/report.py` | L | 2.4 (PDF export) |

### Phase 4: Enterprise Features (8-12 weeks)

| # | Item | Description | Technical Approach | Complexity | Dependencies |
|---|------|-------------|-------------------|-----------|--------------|
| 4.1 | **Authentication system** | Basic login with password, session management | Reflex auth middleware, bcrypt password hashing | L | None (but critical for production) |
| 4.2 | **REST API layer** | Expose BIAI capabilities for embedded analytics | New: `biai/api/routes.py`, `biai/api/auth.py` (API key auth) | L | 4.1 (authentication) |
| 4.3 | **Additional DB connectors** | MySQL, SQLite, SQL Server via plugin interface | New: `biai/db/mysql.py`, `biai/db/sqlite.py`, `biai/db/mssql.py` | L | Plugin interface design |
| 4.4 | **Plugin system** | Extensible chart types, connectors, AI processors | New: `biai/plugins/` directory, plugin discovery, interface definitions | XL | None |
| 4.5 | **Webhook alerts** | Metric threshold alerts via webhook (Slack, Teams, email) | New: `biai/utils/webhook.py`, `biai/models/alert.py` | M | 3.12 (report scheduler) |
| 4.6 | **Query audit logging** | Log all executed queries with user, timestamp, results for compliance | New: `biai/utils/audit_log.py` | M | 4.1 (authentication for user tracking) |
| 4.7 | **Dashboard sharing** | Generate shareable URL encoding dashboard state | Modify `biai/state/dashboard.py`, URL state serialization | L | 4.1 (authentication) |
| 4.8 | **Reinforcement Fine-Tuning** | Fine-tune domain-specific model via Fireworks AI RFT | New: `biai/ai/fine_tuning.py`, training pipeline | XL | 1.6 (query history as training data) |

---

## 9. Technical Specifications

### Spec 1: Multi-Model Router (`biai/ai/model_router.py`)

**Purpose:** Automatically select the most cost-effective LLM for each query based on estimated complexity.

**Data model:**
```python
class QueryComplexity(Enum):
    SIMPLE = "simple"      # score 1-3
    MEDIUM = "medium"      # score 4-6
    COMPLEX = "complex"    # score 7-10

class ModelTier(Enum):
    LOCAL_PRIMARY = "local_primary"       # Qwen3-Coder:30b
    LOCAL_SECONDARY = "local_secondary"   # GPT-OSS-20B
    CLOUD_BUDGET = "cloud_budget"         # DeepSeek V3.2 / Groq
    CLOUD_PREMIUM = "cloud_premium"       # Claude Sonnet 4.5

class ModelRouter:
    def __init__(self, configs: list[ModelConfig]): ...

    def classify_complexity(self, question: str, schema: SchemaSnapshot) -> QueryComplexity:
        """Score query complexity based on heuristics."""
        score = 0
        # Count referenced tables (from schema context)
        score += min(len(detected_tables), 5)
        # Detect complex keywords
        if any(kw in question.lower() for kw in ["compare", "trend", "growth rate", "percentage"]):
            score += 2
        # Detect aggregation needs
        if any(kw in question.lower() for kw in ["total", "average", "count", "sum", "max", "min"]):
            score += 1
        # Detect time-based analysis
        if any(kw in question.lower() for kw in ["by month", "over time", "this year", "last quarter"]):
            score += 1
        return QueryComplexity based on score

    def select_model(self, complexity: QueryComplexity) -> ModelConfig:
        """Return the optimal model for given complexity."""

    def escalate(self, current_tier: ModelTier) -> ModelConfig | None:
        """Return next tier model for fallback."""
```

**Integration point:** Modify `SelfCorrectionLoop.run()` to call `model_router.escalate()` after 2 consecutive failures.

**UI changes:** `biai/components/chat_message.py` — Show model badge (e.g., "Qwen3-Local" or "Claude-Cloud") on each response.

### Spec 2: Cross-Filtering System (`biai/state/filter.py`)

**Purpose:** Click on any chart element to filter all related widgets on the dashboard.

**Data model:**
```python
class ActiveFilter:
    column: str          # e.g., "status"
    value: str | list    # e.g., "Active" or ["Active", "Pending"]
    source_widget_id: str
    created_at: datetime

class FilterState(rx.State):
    active_filters: list[dict]  # Serialized ActiveFilter list

    def apply_filter(self, column: str, value: str, source_id: str):
        """Add a filter, notify all widgets."""

    def remove_filter(self, column: str):
        """Remove filter by column."""

    def clear_all_filters(self):
        """Reset all filters."""
```

**ECharts integration:** Add `dispatch` event handler to chart options:
```javascript
// Injected via echarts_builder.py
myChart.on('click', function(params) {
    // Send dimension name and value back to Reflex state
    reflex.call('FilterState.apply_filter', params.name, params.seriesName, widgetId);
});
```

**Widget response:** Each widget's data source applies active filters as WHERE clauses (client-side DataFrame filtering for cached results, or re-query with additional WHERE for live data).

### Spec 3: Query Result Cache (`biai/utils/query_cache.py`)

**Purpose:** Cache query results to avoid redundant database hits.

```python
from cachetools import TTLCache
import hashlib

class QueryCache:
    def __init__(self, maxsize: int = 100, ttl: int = 300):
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._stats = {"hits": 0, "misses": 0}

    def _make_key(self, sql: str, connection_hash: str) -> str:
        return hashlib.sha256(f"{sql}|{connection_hash}".encode()).hexdigest()

    def get(self, sql: str, connection_hash: str) -> QueryResult | None:
        key = self._make_key(sql, connection_hash)
        result = self._cache.get(key)
        if result:
            self._stats["hits"] += 1
        else:
            self._stats["misses"] += 1
        return result

    def put(self, sql: str, connection_hash: str, result: QueryResult):
        key = self._make_key(sql, connection_hash)
        self._cache[key] = result

    def invalidate_all(self):
        self._cache.clear()

    @property
    def hit_rate(self) -> float:
        total = self._stats["hits"] + self._stats["misses"]
        return self._stats["hits"] / total if total > 0 else 0.0
```

**Integration:** Modify `QueryExecutor.execute()` to check cache before DB query. Show "Cached" badge on cached results.

### Spec 4: PDF Export (`biai/utils/pdf_export.py`)

**Purpose:** Generate PDF reports with charts, tables, and AI narrative.

**Technical approach:** HTML template → weasyprint → PDF

```python
from weasyprint import HTML
from jinja2 import Template

class PDFExporter:
    def __init__(self, template_path: str = "biai/templates/report.html"):
        self.template = Template(open(template_path).read())

    async def export(
        self,
        title: str,
        charts: list[str],      # Base64-encoded chart images
        tables: list[dict],      # {columns, rows}
        narrative: str,          # AI-generated text
        kpis: list[dict],       # {name, value, change}
    ) -> bytes:
        html = self.template.render(
            title=title,
            date=datetime.now().strftime("%Y-%m-%d"),
            charts=charts,
            tables=tables,
            narrative=narrative,
            kpis=kpis,
        )
        return HTML(string=html).write_pdf()
```

**Chart image capture:** Use ECharts `getDataURL()` via `evaluate_script()` or render server-side with `pyecharts` to get PNG base64.

**New file:** `biai/templates/report.html` — Jinja2 HTML template with CSS for print layout.

### Spec 5: Enhanced KPI Card (`biai/components/kpi_card.py`)

**Current:** Shows metric name and value for single-row results.

**New design:**
```
+------------------------------------------+
|  [icon]  Revenue This Month              |
|                                          |
|     $1,247,892                          |
|                                          |
|  ▲ +12.3% vs last month                |
|  ~~~~~~~~ (sparkline)                   |
|  Target: 85% achieved                   |
+------------------------------------------+
```

**Data model additions:**
```python
class KPIData:
    name: str
    value: float | str
    formatted_value: str
    change_pct: float | None         # Period-over-period %
    change_direction: str | None     # "up", "down", "flat"
    sparkline_data: list[float]      # Historical values for sparkline
    target: float | None             # Target value
    target_pct: float | None         # % of target achieved
```

**Sparkline rendering:** Inline SVG path element (no full chart library needed):
```python
def sparkline_svg(data: list[float], width: int = 80, height: int = 20) -> str:
    """Generate SVG sparkline path from data points."""
    ...
```

### Spec 6: Sankey Chart Builder (`biai/ai/echarts_builder.py` extension)

**ECharts option structure:**
```python
def _build_sankey(self, df: pd.DataFrame, config: ChartConfig) -> dict:
    # Expects df with columns: source, target, value
    nodes = list(set(df["source"].tolist() + df["target"].tolist()))
    links = [
        {"source": row["source"], "target": row["target"], "value": row["value"]}
        for _, row in df.iterrows()
    ]
    return {
        "tooltip": {"trigger": "item"},
        "series": [{
            "type": "sankey",
            "layout": "none",
            "emphasis": {"focus": "adjacency"},
            "data": [{"name": n} for n in nodes],
            "links": links,
            "lineStyle": {"color": "gradient", "curveness": 0.5},
            "label": {"color": "#e2e8f0"},
        }]
    }
```

**Chart advisor heuristic:** Recommend Sankey when:
- DataFrame has exactly 3 columns
- Two columns are string/categorical (source, target)
- One column is numeric (value/count)
- Column names contain: "from", "to", "source", "target", "transition"

### Spec 7: Suggestion Engine (`biai/ai/suggestion_engine.py`)

**Purpose:** Generate context-aware follow-up questions after each query result.

```python
class SuggestionEngine:
    def generate(
        self,
        question: str,
        sql: str,
        df: pd.DataFrame,
        schema: SchemaSnapshot,
        insights: list[Insight],
    ) -> list[str]:
        """Generate 3-5 follow-up questions."""
        suggestions = []

        # Data shape based
        if has_time_column(df):
            suggestions.append(f"Show the trend of {numeric_cols[0]} over time")

        # Insight based
        for insight in insights:
            if insight.type == "anomaly":
                suggestions.append(f"What happened around {insight.context['period']}?")
            if insight.type == "pareto":
                suggestions.append(f"Show details for the top {insight.context['top_n']} items")

        # Schema relationship based
        for fk in schema.foreign_keys_from(current_table):
            suggestions.append(f"Break down by {fk.referenced_table}")

        # Aggregation expansion
        if "GROUP BY" in sql:
            suggestions.append("Show the detailed records behind these numbers")

        return suggestions[:5]
```

### Spec 8: Process Metrics Calculator (`biai/ai/process_metrics.py`)

```python
@dataclass
class ProcessMetrics:
    total_cases: int
    avg_cycle_time: timedelta
    median_cycle_time: timedelta
    per_activity_duration: dict[str, timedelta]
    bottleneck_activity: str
    bottleneck_duration: timedelta
    rework_rate: dict[str, float]  # activity -> % of cases with rework
    happy_path_conformance: float  # % of cases following most common path

class ProcessMetricsCalculator:
    def calculate(self, event_log: pd.DataFrame) -> ProcessMetrics:
        """
        event_log columns: case_id, activity, timestamp, [resource]
        """
        # Cycle time: max(timestamp) - min(timestamp) per case
        # Per-activity: next_timestamp - current_timestamp per activity
        # Bottleneck: activity with max average duration
        # Rework: cases where same activity appears >1 time
        # Conformance: most common activity sequence vs actual
```

### Spec 9: Event Log Builder (`biai/ai/event_log_builder.py`)

```python
class EventLogBuilder:
    async def build_from_history_table(
        self, connector: DatabaseConnector, table: str, schema: SchemaSnapshot
    ) -> pd.DataFrame:
        """
        Detect pattern: (entity_id, status/action, timestamp, [actor])
        Return standardized event log: case_id, activity, timestamp, resource
        """
        # 1. Identify case_id column (FK to main entity)
        # 2. Identify activity column (status, action, event_type)
        # 3. Identify timestamp column (created_at, event_date)
        # 4. Identify resource column (user_id, assigned_to) - optional
        # 5. Query and standardize

    async def build_from_status_column(
        self, connector: DatabaseConnector, table: str,
        status_col: str, timestamp_col: str, id_col: str
    ) -> pd.DataFrame:
        """
        For tables with current status only (no history):
        Reconstruct transitions by comparing snapshots or using updated_at.
        """
```

### Spec 10: Cloud Provider Abstraction (`biai/ai/cloud_providers.py`)

```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system: str, **kwargs) -> str: ...

    @abstractmethod
    async def stream(self, prompt: str, system: str, **kwargs) -> AsyncIterator[str]: ...

class OllamaProvider(LLMProvider):
    """Current Ollama integration — wraps existing vanna_client."""

class GroqProvider(LLMProvider):
    """Groq API with OpenAI-compatible endpoint."""
    def __init__(self, api_key: str, model: str = "gpt-oss-20b"):
        self.client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)

class AnthropicProvider(LLMProvider):
    """Claude API for premium queries."""
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        self.client = AsyncAnthropic(api_key=api_key)

class DeepSeekProvider(LLMProvider):
    """DeepSeek API — ultra-cheap cloud option."""
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.client = AsyncOpenAI(base_url="https://api.deepseek.com/v1", api_key=api_key)
```

**Integration with Vanna:** Create a `MultiModelVanna` subclass that delegates `generate_sql()` to the appropriate provider based on model router decision, while still using ChromaDB for RAG retrieval.

---

## 10. Risk Assessment

### 10.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Reflex 0.8.x breaking changes** | Medium | High | Pin Reflex version; test against RC releases; maintain upgrade branch |
| **Vanna 2.0 migration breaks existing pipeline** | Medium | High | Keep Vanna 1.x as fallback; migration on separate branch; comprehensive test suite |
| **Cloud API rate limits / outages** | Low | Medium | Graceful fallback to local model; retry with exponential backoff |
| **ECharts Sankey rendering issues** | Low | Low | Plotly Sankey as fallback (already supported) |
| **State serialization issues with new features** | Medium | Medium | Continue `__getstate__` pattern; avoid storing non-serializable objects in state; use `_` prefix vars carefully |
| **Memory pressure from query caching** | Low | Medium | TTL eviction + maxsize limit; monitor memory usage |
| **LLM routing classifier accuracy** | Medium | Low | Start with simple heuristics; refine with user feedback; manual override option |

### 10.2 Performance Considerations

| Concern | Current State | After Evolution | Mitigation |
|---------|--------------|-----------------|------------|
| **Schema training time** | 30-60s per connection | 5-10s (incremental) | Schema caching + differential training |
| **Query response time** | 3-5s (LLM generation) | 2-4s local, <1s cached | Query caching, model routing (fast models for simple queries) |
| **Memory usage** | ~500MB (Reflex + state) | ~800MB (+ cache, history) | LRU eviction, lazy loading, pagination |
| **VRAM usage** | ~8GB (Qwen3-Coder:30b) | ~16GB (if dual model) | Only load one model at a time; swap on demand |
| **ChromaDB training** | Full reset on each connect | Incremental updates | Persistent collections, diff-based updates |
| **PDF generation** | N/A (new feature) | 2-5s per report | Background task, progress indicator |

### 10.3 Compatibility Concerns

| Concern | Details | Mitigation |
|---------|---------|------------|
| **Reflex version upgrades** | Reflex is actively evolving (0.8.x → 0.9.x) | Comprehensive test suite; avoid undocumented APIs |
| **Ollama API changes** | Ollama API is stable but models change frequently | Abstract model access behind provider interface |
| **Browser compatibility** | ECharts + React Flow require modern browsers | Target Chrome/Edge/Firefox latest 2 versions |
| **Python version** | Currently works on Python 3.11+ | Test against 3.12, 3.13 |
| **Windows vs Linux** | Current dev on Windows; deployment may be Linux | Use pathlib consistently; avoid Windows-specific paths |

### 10.4 Migration Path from Current Architecture

**Phase 1 changes are additive** — no existing code is removed or broken. New files are added, existing files get minor modifications. Safe to deploy incrementally.

**Phase 2 requires careful sequencing:**
1. Multi-model router wraps existing `SelfCorrectionLoop` — old behavior is default
2. Cloud API integration is opt-in via settings
3. Cross-filtering adds new events but doesn't change existing widget rendering
4. PDF/Excel export are standalone utilities

**Phase 3 has higher risk:**
1. Process mining extensions depend on new event log builder — test thoroughly with real data
2. Vanna 2.0 migration should be on a separate branch with A/B comparison
3. Conversational commands add a new intent parser before the existing pipeline

**Phase 4 is architectural:**
1. Authentication system touches all pages — plan for a dedicated sprint
2. Plugin system requires careful API design — release as beta first
3. REST API layer requires security review before production use

### 10.5 Key Dependencies

```
Phase 1: No external dependencies (all additive)
Phase 2:
  - weasyprint or reportlab (PDF export)
  - openpyxl (Excel export)
  - anthropic, openai Python SDKs (cloud APIs)
Phase 3:
  - statsmodels (time series forecasting)
  - APScheduler (report scheduling)
Phase 4:
  - bcrypt (authentication)
  - Additional DB drivers: pymysql, pyodbc, sqlite3 (already in stdlib)
```

---

## Appendix A: Research Report References

Throughout this plan, recommendations are grounded in specific findings from the three research reports:

| Finding | Source | Plan Section |
|---------|--------|-------------|
| Qwen3-Coder:30b ~50 t/s on RTX 4090, 8GB VRAM | LLM Research 4.1 | 2.1 Primary Local Model |
| GPT-OSS-20B ~60 t/s, 16GB VRAM, "Very Good" SQL | LLM Research 4.4 | 2.2 Secondary Model |
| Claude Sonnet 4.5 94% BIRD accuracy, $3/1M input | LLM Research 2.2, 5.1 | 2.3 Cloud API |
| Multi-model routing reduces cost 95%+ vs always-cloud | LLM Research 8.1 | 2.4 Routing Architecture |
| Fireworks AI RFT: 7B fine-tuned beats GPT-4o on domain SQL | LLM Research 5.7 | 8 Phase 4 (4.8) |
| Vanna 2.0 agent framework, streaming, RBAC | LLM Research 9.1 | 2.5 RAG Improvements |
| KPI card anatomy: value + trend + sparkline + comparison | BI Research 13.1 | 3.4 KPI System |
| Cross-filtering: major gap, standard in all commercial BI | BI Research 14, App Analysis 5 | 3.2 Interactive Features |
| Sankey diagrams: Plotly native, ECharts native | BI Research 5.2 | 3.2 New Chart Types |
| BPMN visualization libraries for process mining | BI Research 6.4 | 3.3 Process Flow Upgrades |
| PDF/Excel export: standard in all competitors | BI Research 10, App Analysis 5 | 3.5 Report Generation |
| 15 state classes, ChatState ~590 LOC (monolith) | App Analysis 3.2, 6.1 | 7 Architecture Evolution |
| No authentication (CRITICAL security gap) | App Analysis 6.5 | 8 Phase 4 (4.1) |
| No query result caching | App Analysis 6.4 | 8 Phase 1 (1.4) |
| Schema training 30-60s per connection | App Analysis 6.4 | 7.3.2 Incremental Schema |
| AI-native BI: semantic layer is critical success factor | BI Research 3.3 | 2.5 RAG Improvements |
| ThoughtSpot Spotter: agent-based multi-step analysis | BI Research 1.4 | 4.5 Conversational Analytics |
| Gartner: 75% of data stories auto-generated by 2025 | BI Research 11.1 | 4.3 Data Storytelling |
| Process mining market: 80% of orgs embed by 2025 | BI Research 6.1 | 5 Process Mining 2.0 |

## Appendix B: Current vs Target Feature Matrix

| Feature | Current BIAI | BIAI 2.0 Target | Phase |
|---------|-------------|-----------------|-------|
| Local LLM models | 1 (Qwen3-Coder:30b) | 3+ local + 3 cloud | P1-P2 |
| Chart types | 16 (13 ECharts + Plotly) | 22+ (+ Sankey, box, candlestick, etc.) | P1-P2 |
| Cross-filtering | None | Full dashboard cross-filter | P2 |
| Drill-down | None | Hierarchical (time, category) | P2 |
| KPI cards | Basic (value only) | Sparkline + trend + comparison + target | P1 |
| Export formats | CSV only | CSV + Excel + PDF | P2 |
| Query caching | None | TTL LRU cache | P1 |
| Schema training | Full reset every time | Incremental with caching | P2 |
| Process viz | React Flow only | + Sankey, swimlane, timeline | P1-P3 |
| Process metrics | None | Cycle time, bottleneck, rework, conformance | P3 |
| Forecasting | None | Holt-Winters with confidence bands | P3 |
| Authentication | None | Basic password auth | P4 |
| API layer | None | REST API with key auth | P4 |
| Keyboard shortcuts | None | Full shortcut set + command palette | P1-P3 |
| Query history | In-memory only | Persistent with search | P1 |
| Responsive layout | Fixed percentages | Breakpoint-based responsive | P2 |
| Report scheduling | None | APScheduler with PDF delivery | P3 |
| Collaboration | None | Shared dashboards, URL sharing | P4 |

---

*End of BIAI Evolution Plan*

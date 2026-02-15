# Research Report: Modern Business Intelligence Systems — UI/UX, Data Visualization & Process Flows

**Date:** 2026-02-14
**Author:** BI Research Agent
**Scope:** Commercial BI leaders, open-source BI, AI-native BI (2025-2026), process mining, visualization patterns

---

## Table of Contents

1. [Commercial BI Leaders](#1-commercial-bi-leaders)
2. [Open-Source BI Tools](#2-open-source-bi-tools)
3. [AI-Native BI (New Wave 2025-2026)](#3-ai-native-bi-new-wave-2025-2026)
4. [Dashboard Design Patterns](#4-dashboard-design-patterns)
5. [Chart & Visualization Types](#5-chart--visualization-types)
6. [Process Flow & Workflow Visualization](#6-process-flow--workflow-visualization)
7. [Schema Exploration & ERD Visualization](#7-schema-exploration--erd-visualization)
8. [Natural Language to SQL Interfaces](#8-natural-language-to-sql-interfaces)
9. [Real-Time Data Visualization](#9-real-time-data-visualization)
10. [Export Capabilities](#10-export-capabilities)
11. [Annotation & Data Storytelling](#11-annotation--data-storytelling)
12. [AI-Powered Insights & Recommendations](#12-ai-powered-insights--recommendations)
13. [KPI Cards & Scorecards](#13-kpi-cards--scorecards)
14. [Drill-Down & Interactive Filtering](#14-drill-down--interactive-filtering)
15. [Color Palettes & Design Systems](#15-color-palettes--design-systems)
16. [Animation Patterns in Charts](#16-animation-patterns-in-charts)
17. [Collaborative & Sharing Features](#17-collaborative--sharing-features)
18. [Recommendations for BIAI Evolution](#18-recommendations-for-biai-evolution)

---

## 1. Commercial BI Leaders

### 1.1 Tableau (Salesforce)

**Strengths:**
- Industry-leading visualization engine with 50+ chart types
- Three dashboard design clusters identified in research (25,000 dashboards analyzed):
  - **Analytic** — predominantly charts and widgets (most common)
  - **Magazine** — static with prominent text commentary around charts
  - **Infographic** — visual storytelling with custom graphics
- Layout: tiled containers (single-layer grid, responsive) and floating containers (layered, manual positioning)
- Interactive patterns: widget-to-chart filters (69%), chart-to-chart cross-filtering (46%), legend-to-chart filtering (43%)
- **Tableau Pulse** (2024.1+): next-gen NL querying with conversational abilities
- **Tableau Next**: semantic AI integration for deeper natural language understanding
- Salt Design System for consistent UI patterns
- Dashboard Extensions marketplace for custom widgets

**Visualization Library:** Proprietary VizQL engine
**NL Interface:** Tableau Pulse / Tableau Next (semantic AI)
**Process Viz:** Limited native support; relies on extensions

### 1.2 Microsoft Power BI

**Strengths:**
- Deepest Microsoft ecosystem integration (Excel, Azure, SharePoint, Teams)
- Drag-and-drop dashboard builder; no advanced technical skills needed
- **Copilot Integration** (2025-2026):
  - Natural language Q&A with generative AI
  - DAX expression generation from natural language
  - Semantic model building via natural language
  - Report and semantic model attachment for grounded answers
  - Three chat experiences: standalone Copilot, Copilot pane (in reports), Copilot in apps
- Legacy Q&A deprecated (retiring December 2026) in favor of Copilot
- Paginated reports for pixel-perfect export (PDF, Excel, Word, CSV, XML)
- Real-time streaming via push datasets, streaming datasets, PubNub
- Native in-context commenting on dashboards, reports, and individual visuals
- Workspaces as collaboration foundation (2026)

**Visualization Library:** Custom visuals ecosystem + D3.js based
**NL Interface:** Copilot (GPT-powered), replacing Q&A
**Process Viz:** Visio integration, custom visuals
**Pricing:** $10-$14/user/month (Pro), $20/user/month (Premium Per User)

### 1.3 Google Looker

**Strengths:**
- Data modeling via LookML (code-first approach)
- Embedded analytics specialization
- Scalable, governed, AI-integrated features
- **Conversational Analytics API** for natural language AI
- Part of Google Cloud ecosystem (BigQuery integration)

**Visualization Library:** Proprietary + custom viz
**NL Interface:** Conversational Analytics API (Google AI)

### 1.4 ThoughtSpot

**Strengths:**
- AI-native analytics built entirely around search
- **ThoughtSpot Sage** (deprecated 2025, replaced by **Spotter**):
  - Combined GPT NLP with ThoughtSpot's relational search
  - Supplemented GPT with schema metadata (columns, synonyms, join paths, formulas)
  - Generated business-ready SQL from natural language
- **Spotter Agent** (2025+): next-gen AI data exploration
  - More powerful exploration and confident decision-making
  - Agent-based architecture for multi-step analysis

**Visualization Library:** Proprietary
**NL Interface:** Spotter Agent (evolved from Sage)
**Key Innovation:** Search-first paradigm; zero SQL knowledge required

### 1.5 Qlik Sense

**Strengths:**
- Associative engine (explores all data relationships, not just predefined queries)
- 160+ data source connectors
- 2025 AI services: Qlik Answers (gen-AI assistant), Qlik Predict (no-code ML), Qlik Automate
- New sheet-editing experience, improved tables with shape labels and custom CSS
- Strong in guided analytics and storytelling

**Visualization Library:** Proprietary
**NL Interface:** Qlik Answers (generative AI assistant)

### 1.6 Sisense

**Strengths:**
- Embedded analytics focus (white-label dashboards in apps)
- **Sisense Intelligence** (2025): AI tools for accelerated dashboard creation
- New Analytical Engine: optimized queries, expanded SQL support
- Directional relationships and cloud-native Elasticube Cloud
- Best for OEM/embedded use cases

**Visualization Library:** Proprietary + extensible
**NL Interface:** AI-powered query assistant

### 1.7 Domo

**Strengths:**
- 1,000+ built-in data connectors
- AI-powered automated insights for trend detection
- **Domo App Studio**: custom apps without coding
- Branded visualizations (custom colors, logos, fonts)
- Strong mobile experience

**Visualization Library:** Proprietary
**NL Interface:** AI-assisted querying

### 1.8 Mode Analytics

**Strengths:**
- SQL-first approach for data analysts
- Python/R notebooks integrated into reports
- Collaborative report building
- Strong for data teams that prefer code-based workflows

---

## 2. Open-Source BI Tools

### 2.1 Apache Superset

**Strengths:**
- Broadest visualization catalog among open-source tools
- Chart types include: heatmaps, time-series, sunburst, treemaps, pivot tables, **Sankey diagrams**, geographic maps, box plots, word clouds
- SQL-first approach with "Datasets" (fields, metrics, calculated columns)
- Reusable dataset definitions and metric/dimension modeling
- Fine-grained RBAC, row-level security filters
- Highly configurable Explore settings for complex, exploratory analysis
- Active Apache Foundation community

**Best For:** Complex exploratory analytics, organizations with strong data governance
**Limitation:** Steeper learning curve than Metabase

### 2.2 Metabase

**Strengths:**
- Fastest setup among open-source tools (single JAR file)
- Click-based exploration (no SQL required for basic use)
- Essential chart types: bar, line, area, pie, tables, maps, gauges
- Group-based permissions with approachable admin model
- Good for business user self-service
- Recent AI integration for question answering

**Best For:** Business users, quick self-service analytics
**Limitation:** Fewer advanced visualization types than Superset

### 2.3 Redash

**Strengths:**
- 35+ SQL and NoSQL data source support
- Query editor with schema browser and auto-complete
- Visualization types: chart, cohort, pivot table, boxplot, map, counter, **Sankey**, sunburst, word cloud
- Drag-and-drop dashboard creation
- API access for extensibility
- Data alerts for proactive monitoring
- Easy sharing via direct links, embedded dashboards, scheduled reports

**Best For:** SQL-savvy teams wanting quick dashboarding

### 2.4 Lightdash

**Strengths:**
- AI-first, open-source BI platform
- Git-native (direct connection to dbt models)
- Define metrics once, get instant trustworthy insights
- Strong dbt ecosystem integration
- Version-controlled analytics definitions

**Best For:** dbt-centric data teams

### 2.5 Evidence.dev

**Strengths:**
- BI-as-code approach (Markdown + SQL)
- Git-based workflow (version control, CI/CD)
- Static site generation for reports
- Developer-friendly (code review, pull requests for analytics)

**Best For:** Developer teams wanting code-first BI

### 2.6 Rill Data

**Strengths:**
- Dashboards from SQL + YAML files only
- CLI for local development
- Local web UI for drafting queries/dashboards
- Cloud deployment option
- Extremely fast for OLAP-style exploration

**Best For:** Rapid metric exploration, developer-friendly

---

## 3. AI-Native BI (New Wave 2025-2026)

### 3.1 Market Overview

The global conversational AI market grew from USD 14.3 billion in 2025 to a projected USD 41.39 billion by 2030. NL interfaces are becoming the primary way users interact with data.

### 3.2 Key Players

#### Supaboard
- **Agentic BI platform** that understands business context, not just data
- Unified layer for metrics, definitions, and business logic
- 600+ data source connections
- Ask questions in plain English; instantly generate dashboards and reports
- Focus on trusted, governed insights

#### Querio
- Plain English to SQL with a **context layer** (unified business glossary)
- Standardized table relationships and metrics across the organization
- Live data connections (no stale extracts)
- Governed analytics for BI teams
- Competitive pricing vs Julius and BlazeSQL

#### BlazeSQL
- AI Data Analytics chatbot (ChatGPT for SQL databases)
- Cuts SQL query time by up to 85%
- Integrates with MySQL, Snowflake, PostgreSQL
- AI-generated dashboards
- Privacy-focused: only accesses metadata

#### Holistics
- AI-powered insights through natural language conversations
- Addresses accuracy/reliability problems common in AI BI tools
- Git-native version control for models and dashboards
- Semantic layer for governed responses

### 3.3 Critical Success Factors for AI-Native BI

1. **Semantic Layer / Business Glossary** — platforms aligning NL questions to governed definitions reduce confusion and return reliable answers
2. **Context Awareness** — remembering previous conversations, proactively suggesting analyses
3. **Accuracy Governance** — verified answers, grounded responses from curated data models
4. **Self-Correction** — ability to retry with error feedback when SQL generation fails
5. **Transparency** — showing generated SQL to users for validation

---

## 4. Dashboard Design Patterns

### 4.1 Layout Patterns

| Pattern | Description | Use Case |
|---------|-------------|----------|
| **Z-Layout** | Important content top-left, flows right and down | General dashboards |
| **F-Layout** | Users scan left-to-right, top-to-bottom (Western reading) | Text-heavy dashboards |
| **Hero Section** | KPI cards at top, detail charts below | Executive dashboards |
| **Grid-based** | Fixed-size tiles in responsive grid | Multi-metric monitoring |
| **Split-screen** | Left panel (nav/filters) + right panel (content) | Exploratory analytics |

### 4.2 Dashboard Design Clusters (Tableau Research, 25K dashboards)

1. **Analytic** (most common) — predominantly charts, widgets, terse text blocks
2. **Magazine** — static, prominent text commentary around chart blocks
3. **Infographic** — custom visuals, storytelling-focused

### 4.3 Container Types

- **Tiled containers** — non-overlapping, single-layer grid, responsive to size changes
- **Floating containers** — layered over other objects, manually resizable

### 4.4 Widget Types (Common across platforms)

| Widget | Purpose |
|--------|---------|
| KPI Card | Single metric with trend |
| Line Chart | Time series trends |
| Bar Chart | Categorical comparisons |
| Pie/Donut Chart | Part-of-whole |
| Data Table | Detailed row-level data |
| Map | Geographic data |
| Gauge | Progress toward target |
| Scatter Plot | Correlation analysis |
| Heatmap | Density/intensity patterns |
| Treemap | Hierarchical data |
| Sankey Diagram | Flow/transition data |
| Pivot Table | Multi-dimensional analysis |
| Filter/Slicer | Interactive data filtering |
| Text/Markdown | Commentary and context |

### 4.5 Best Practices

- White space and padding to delineate sections
- Interactive elements must be discoverable and predictable
- Simplified design that makes complex decisions easier
- 5-7 KPIs maximum per dashboard
- Responsive design for multiple screen sizes
- Visual hierarchy: larger fonts for values, smaller for context

---

## 5. Chart & Visualization Types

### 5.1 Comprehensive Chart Type Inventory

**Basic Charts:**
- Line, Bar (horizontal/vertical, stacked, grouped), Area, Pie, Donut, Scatter, Bubble

**Advanced Charts:**
- Heatmap, Treemap, Sunburst, Sankey Diagram, Waterfall, Funnel, Radar/Spider

**Statistical:**
- Box Plot, Histogram, Violin Plot, Error Bars

**Geographic:**
- Choropleth Map, Point Map, Flow Map, Bubble Map

**Time-Series:**
- Sparkline, Area Range, Candlestick (financial)

**Hierarchical:**
- Treemap, Sunburst, Icicle, Tree Diagram

**Flow/Process:**
- Sankey Diagram, Alluvial Diagram, Network Graph, Flowchart

**Table Variants:**
- Pivot Table, Data Grid, Cohort Table

### 5.2 Plotly.js Capabilities (Relevant to BIAI)

Plotly.js (used by BIAI via `rx.plotly()`) supports:

- **Sankey Diagrams**: `go.Sankey` with source/target/value/label; node arrangement modes (snap, perpendicular, freeform, fixed); circular flow detection (Tarjan's algorithm)
- **Treemaps**: `go.Treemap` with hierarchy via labels/parents; click-to-zoom drill-down; pathbar for navigation
- **Sunburst**: hierarchical radial chart with drill-down
- **Funnel**: conversion pipeline visualization
- All standard chart types (bar, line, scatter, pie, etc.)
- Interactive features: hover tooltips, zoom, pan, selection, crosshair

### 5.3 Library Comparison

| Library | Interactivity | Chart Types | React Support | Self-hosted |
|---------|--------------|-------------|---------------|-------------|
| Plotly.js | High | 50+ | Yes | Yes |
| D3.js | Highest (custom) | Unlimited | Manual | Yes |
| Chart.js | Medium | 8 basic | Yes | Yes |
| ECharts | High | 30+ | Yes | Yes |
| Vega-Lite | Medium | 20+ | Yes | Yes |

---

## 6. Process Flow & Workflow Visualization

### 6.1 Process Mining Industry (2025)

**Market Size:** Gartner lists 40+ tools in process mining platforms. By 2025, 80% of organizations are expected to embed process mining in at least 10% of operations.

**Key Players:**
- **Celonis** — market leader; creates digital twin of processes from event logs; visualizes "happy path" and all variants; real-time process monitoring
- **Fluxicon Disco** — desktop tool for fast process discovery and visualization
- **iGrafx Process360 Live** — unifies process modeling, mining, and simulation

### 6.2 Visualization Approaches for Processes

| Approach | Description | Best For | Libraries |
|----------|-------------|----------|-----------|
| **Sankey Diagram** | Flow volumes between nodes | Volume-based processes, transitions | Plotly.js, D3.js |
| **Flowchart** | Sequential steps with decisions | Simple linear processes | React Flow, Mermaid.js |
| **BPMN Diagram** | Standard business process notation | Formal process documentation | bpmn-visualization, bpmn.io |
| **Swimlane Diagram** | Lanes per actor/department | Cross-functional processes | Syncfusion, DHTMLX, React Flow |
| **Network Graph** | Nodes and edges | Complex relationships | React Flow, vis.js, cytoscape.js |
| **Process Map (variant)** | Discovered process with metrics | Process mining results | Custom (D3, React Flow) |
| **Alluvial Diagram** | Multi-stage flow | Status transitions over time | Plotly (Sankey variant) |

### 6.3 React Flow (XyFlow) — Primary Process Viz Library

**Version:** v12+ (rebranded as XyFlow)
**License:** MIT
**Key Features:**
- Nodes are React components (fully customizable)
- 4 edge types: Bezier, Step, SmoothStep, Straight
- Built-in: drag-and-drop, zooming, panning, multi-select
- Sub-flows and nested graphs
- Minimap, controls, background patterns
- Used for: workflow automation, data processing tools, chatbot builders

**Extensions:**
- `@liangfaan/reactflow-swimlane` — swimlane flowcharts with Dagre algorithm
- Overflow component library — advanced diagram logic

### 6.4 BPMN Visualization Libraries

- **bpmn-visualization** (TypeScript/R) — visualize process mining results on BPMN models
- **bpmn.io** — full BPMN modeling and rendering
- Both support overlays for metrics (e.g., case count, average duration per activity)

### 6.5 Process Mining Visualization Patterns (Celonis)

1. **Process Map** — nodes = activities, edges = transitions, width proportional to case count
2. **Variant Explorer** — compare actual paths vs "happy path"
3. **Conformance Overlay** — highlight deviations from expected process
4. **Duration Heatmap** — color-code activities by average processing time
5. **Bottleneck Analysis** — identify steps with longest wait times
6. **Rework Detection** — highlight loops and repeated activities

---

## 7. Schema Exploration & ERD Visualization

### 7.1 Approaches in BI Tools

| Tool | Schema Exploration | ERD Visualization |
|------|-------------------|-------------------|
| Power BI | Model view with relationships | Visual relationship editor |
| Tableau | Data pane with hierarchy | Join/relationship diagram |
| Metabase | Schema browser sidebar | X-ray feature (auto-explore) |
| Superset | Dataset explorer | SQL Lab schema browser |
| Qlik | Data model viewer | Associative model view |

### 7.2 Dedicated ERD Tools (React-compatible)

| Tool | Technology | Key Feature |
|------|-----------|-------------|
| **NextERD** | Next.js + React Flow + shadcn/ui | Interactive drag-and-drop ERD |
| **React-ERD** | React component | Simple ERD rendering from schema |
| **DrawDB** | Browser-based | Drag-and-drop + SQL export |
| **ChartDB** | Query-driven | Auto-generates diagrams from schema |
| **Azimutt** | Open-source | Advanced filtering for large schemas |
| **DrawSQL** | SaaS | Visual schema design + DDL export |

### 7.3 Key Features for Schema Exploration

- **Auto-discovery**: Automatically detect tables, columns, relationships
- **Search/filter**: Find tables/columns by name pattern
- **Relationship visualization**: FK arrows between tables
- **Column type indicators**: Icons for PK, FK, nullable, indexed
- **Live connection**: Schema refreshes from actual database
- **Zoom levels**: Overview (table names only) to detail (all columns + types)

---

## 8. Natural Language to SQL Interfaces

### 8.1 Architecture Patterns

| Pattern | Description | Examples |
|---------|-------------|---------|
| **Direct NL2SQL** | LLM generates SQL directly from question + schema | Vanna, BlazeSQL |
| **Semantic Layer** | NL maps to governed metrics/dimensions, then SQL | ThoughtSpot, Looker, Holistics |
| **RAG-enhanced** | Schema DDL + examples in vector store, retrieved for context | Vanna (ChromaDB), Querio |
| **Agent-based** | Multi-step reasoning with tool use | ThoughtSpot Spotter, Power BI Copilot |
| **Self-correcting** | Retry with error feedback | BIAI (current), SQL-of-Thought |

### 8.2 NL2SQL Accuracy Benchmarks (2025-2026)

| Method | Approach | Spider Benchmark | Notes |
|--------|----------|-----------------|-------|
| DIN-SQL | Few-shot prompting | ~33% EX | Careful prompt design + self-correction |
| DAIL-SQL | Few-shot with example selection | ~33% EX | Selects suitable examples per question |
| Oracle AI (Archer 2025) | Reasoning-based | 54.96% EX (English) | Won Archer Challenge by 9+ points |
| SQL-of-Thought | Multi-agent + guided error correction | Higher than baselines | Latest research (2025) |
| GPT-4 (zero-shot) | Direct generation | ~70% EX (Spider) | High cost, cloud-only |

**Key Insight:** Accuracy improves dramatically with:
1. Schema-aware context (DDL, column descriptions, sample values)
2. Self-correction loops (feeding errors back for retry)
3. Semantic layer (governed metric definitions)
4. Example selection (RAG with similar past queries)

### 8.3 BIAI Current Position

BIAI uses Vanna.ai (RAG: ChromaDB + Ollama) with:
- Schema DDL + example queries in vector store
- Self-correction loop (up to 5 retries)
- sqlglot validation + dialect transpilation
- Local inference (Ollama)

**Gaps vs market leaders:**
- No semantic layer / business glossary
- No agent-based multi-step reasoning
- No verified answers or confidence scoring
- No conversation memory across sessions

---

## 9. Real-Time Data Visualization

### 9.1 Approaches

| Approach | Latency | Use Case |
|----------|---------|----------|
| **Push datasets** | Seconds | IoT, monitoring |
| **Streaming datasets** | Sub-second | Live events |
| **Polling** | Minutes | Standard BI refresh |
| **WebSocket** | Real-time | Custom dashboards |

### 9.2 Platform Support

- **Power BI**: Push/streaming datasets, PubNub integration (note: streaming datasets retiring October 2027)
- **Grafana**: Purpose-built for real-time monitoring
- **Superset**: SQL-based refresh on schedule
- **Metabase**: Auto-refresh dashboards (configurable interval)
- **Custom (BIAI opportunity)**: WebSocket + Reflex reactivity for live query results

### 9.3 Trends

- Shift from scheduled refresh to continuous streaming pipelines
- Real-time dashboards enable proactive responses (not just retrospective analysis)
- Integration with event streaming platforms (Kafka, Pulsar)

---

## 10. Export Capabilities

### 10.1 Format Support Matrix

| Format | Power BI | Tableau | Superset | Metabase | Redash |
|--------|----------|---------|----------|----------|--------|
| PDF | Yes | Yes | Yes | Yes | No |
| PNG/Image | Yes | Yes | Yes | Yes | Yes |
| Excel (.xlsx) | Yes (150K rows) | Yes | Yes | Yes | No |
| CSV | Yes | Yes | Yes | Yes | Yes |
| Word | Yes (paginated) | No | No | No | No |
| PowerPoint | Yes | No | No | No | No |
| XML/MHTML | Yes (paginated) | No | No | No | No |

### 10.2 Advanced Export Features

- **Scheduled exports**: Automatic email delivery (Power BI, Tableau, Redash)
- **Paginated reports**: Pixel-perfect multi-page documents (Power BI Report Builder)
- **Embedded exports**: API-driven export for integration
- **Bulk export**: Multiple pages compressed to ZIP (Power BI PNG)

### 10.3 BIAI Current: CSV only
**Gap:** Missing PDF, Excel, PNG dashboard screenshot export

---

## 11. Annotation & Data Storytelling

### 11.1 Market Trend

By 2025, Gartner predicted data stories would be the most widespread way of consuming analytics, with 75% of stories automatically generated using augmented analytics tools.

### 11.2 Features Across Platforms

| Feature | Power BI | Tableau | Yellowfin | Narrative BI |
|---------|----------|---------|-----------|-------------|
| In-visual comments | Yes | Yes | Yes | N/A |
| AI-generated narratives | Copilot | Narrative Science | Built-in | Core feature |
| Annotation on data points | Limited | Yes | Yes | Auto |
| Embedded media (images/video) | No | No | Yes | No |
| Anomaly narration | Copilot | Pulse | Built-in | Core |
| Scheduled story delivery | Yes | Yes | Yes | Yes |

### 11.3 Key Storytelling Patterns

1. **Contextual annotations** — comments on specific data points bridging visualization and narrative
2. **AI-generated summaries** — plain-language explanations of trends and anomalies
3. **Guided narratives** — sequential story with curated visualizations
4. **Embedded reports** — combine charts with images, video, text
5. **Anomaly-driven alerts** — proactive notification of unusual patterns

### 11.4 BIAI Current: Streaming AI text description only
**Gap:** No annotation, no guided storytelling, no anomaly narration

---

## 12. AI-Powered Insights & Recommendations

### 12.1 Capabilities (2025-2026)

| Capability | Description | Platforms |
|-----------|-------------|-----------|
| **Smart chart recommendation** | Auto-select best visualization type | Power BI, Tableau, Superset |
| **Anomaly detection** | Identify outliers and unusual patterns | Zoho Zia, Power BI, Qlik |
| **Trend discovery** | Surface key trends and correlations | All major platforms |
| **Predictive analytics** | Forecast future values | Qlik Predict, Power BI |
| **Natural language summaries** | Generate text explanations of data | Power BI Copilot, Narrative BI |
| **Suggested queries** | Recommend next questions to explore | ThoughtSpot, Querio |
| **Data quality alerts** | Flag data issues | Monte Carlo, Anomaly AI |

### 12.2 Market Impact

- 40% of new BI tool purchases include AI-powered analytics (2025)
- Global data analytics market: $60.5B (2025) -> $143.1B (2035)
- By 2026, AI-powered platforms will handle most routine analysis

### 12.3 BIAI Current: ChartAdvisor (heuristic + LLM-based chart selection)
**Gap:** No anomaly detection, no predictive analytics, no suggested follow-up queries

---

## 13. KPI Cards & Scorecards

### 13.1 Anatomy of a KPI Card

A well-designed KPI card includes:

1. **Date period** — when the metric was measured
2. **Metric name** — clear, descriptive label
3. **Metric value** — large, prominent number (primary visual focus)
4. **Context/comparison** — period-over-period change (%, absolute)
5. **Trend indicator** — arrow (up/down), color (green/red), sparkline
6. **Sparkline** — mini chart showing recent trend

### 13.2 Design Best Practices

- **Font hierarchy**: Largest for value, medium for name, smallest for context
- **Associative colors**: Green = positive, Red = negative, Gray = neutral
- **Icons/emojis**: Enhance quick recognition (arrows, check marks)
- **Hero Section placement**: KPIs at dashboard top for immediate scanning
- **Count**: 5-7 KPIs maximum per view
- **Sans-serif fonts**: Clean readability at all sizes

### 13.3 Scorecard Organization

- Group related KPIs into scorecards
- Include: current value, target/goal, progress percentage, trend line
- Status indicator (on track / at risk / off track)
- KPI icon or gauge visualization

### 13.4 BIAI Current: No KPI cards
**Opportunity:** Add KPI card component with metric value, trend arrow, sparkline, period-over-period comparison

---

## 14. Drill-Down & Interactive Filtering

### 14.1 Cross-Filtering Patterns

1. **Click on visual element** -> filters all related visuals sharing the same dataset
2. **Automatic propagation** -> no manual configuration needed (when enabled)
3. **Hierarchical drill-down** -> Year -> Quarter -> Month -> Week -> Day
4. **Slicer/filter widgets** -> dedicated filter controls (dropdowns, date pickers, sliders)

### 14.2 Implementation Patterns

| Pattern | Description | Platform Example |
|---------|-------------|------------------|
| **Visual cross-filter** | Click bar/segment to filter dashboard | Power BI (default) |
| **Hierarchical drill** | Navigate data hierarchy levels | Tableau, Power BI |
| **Filter panel** | Sidebar with filter widgets | Superset, Metabase |
| **Breadcrumb navigation** | Show current drill path | Plotly treemap pathbar |
| **Context menu** | Right-click for filter/drill options | Qlik Sense |
| **Cascading filters** | Region -> Country -> City | Power BI slicers |

### 14.3 Best Practices

- Cross-filtering should be automatic when visuals share datasets
- Provide clear visual feedback when filters are active
- Include "reset filters" button
- Show filter breadcrumbs/path
- Support both additive (AND) and subtractive (NOT) filtering
- Enable keyboard navigation for accessibility

### 14.4 BIAI Current: No cross-filtering or drill-down
**Gap:** Major gap vs competitors. Dashboard widgets are independent, not interconnected.

---

## 15. Color Palettes & Design Systems

### 15.1 Palette Types for Data Visualization

| Type | Use Case | Example |
|------|----------|---------|
| **Sequential** | Ordered numeric values | Light blue -> Dark blue (dollar amounts over time) |
| **Categorical/Qualitative** | Unrelated categories | Distinct colors per category |
| **Diverging** | Spectrum with midpoint | Red -> White -> Blue (hot to cold) |
| **Alert** | Status indicators | Red (danger), Yellow (warning), Green (ok) |

### 15.2 Design System References

| Design System | Data Viz Colors | Documentation |
|--------------|-----------------|---------------|
| **Carbon** (IBM) | Comprehensive categorical, sequential, diverging palettes | carbondesignsystem.com |
| **Material Design** (Google) | Data visualization guidelines for M2/M3 | m2.material.io, m3.material.io |
| **Pajamas** (GitLab) | Defined data viz color system | design.gitlab.com |
| **Cloudscape** (AWS) | Data vis color foundations | cloudscape.design |
| **USWDS** (US Gov) | Data design standards with colors | xdgov.github.io |
| **Atlassian** | Data viz color selection guide | atlassian.design |
| **Salt** (Tableau) | Layout grid library + design tokens | saltdesignsystem.com |

### 15.3 Best Practices

1. **Accessibility first**: Avoid red/green combos (color blindness); WCAG 4.5:1 contrast for text, 3:1 for large text/UI
2. **Limited palette**: 5-8 colors maximum for categorical data
3. **Saturation control**: Avoid overly saturated colors (eye strain); reserve bold colors for highlighting
4. **Consistent brand**: Same color = same meaning across all dashboards
5. **Data-driven selection**: Match palette type to data structure
6. **Semantic colors**: Red = negative/error, Green = positive/success, Blue = neutral/info

### 15.4 BIAI Current: Default Plotly colors
**Opportunity:** Define custom color palette aligned with BIAI brand; implement design tokens

---

## 16. Animation Patterns in Charts

### 16.1 Effective Animation Types

| Animation | Purpose | Example |
|-----------|---------|---------|
| **Transitions** | Smooth data updates | Bar heights growing on load |
| **Bar Chart Race** | Ranking changes over time | Top 10 categories animated |
| **Line Trace** | Progressive data reveal | Line drawing itself over time |
| **Morphing** | Visual type transitions | Pie -> Bar animation |
| **Highlighting** | Draw attention to key data | Pulsing anomaly point |
| **Loading skeleton** | Content placeholder | Shimmer effect before data loads |

### 16.2 Design Principles

- Animation should **enhance storytelling** and clarify, not decorate
- **Strategic motion** for transitions, trend highlights, context
- Break down data stories progressively to reduce information overload
- Duration: 200-500ms for transitions, 1-3s for narrative animations
- Respect `prefers-reduced-motion` for accessibility

### 16.3 2025 Trends

- Generative motion graphics (algorithm-driven dynamic visualizations)
- Kinetic typography in data storytelling
- Abstract/surreal transitions between dashboard states
- Micro-animations for interactive feedback (hover, click, filter)

### 16.4 BIAI Current: No animations
**Opportunity:** Add loading skeletons, smooth chart transitions, highlighted anomalies

---

## 17. Collaborative & Sharing Features

### 17.1 Feature Matrix

| Feature | Power BI | Tableau | Metabase | Superset |
|---------|----------|---------|----------|----------|
| In-context comments | Yes | Yes | No | No |
| Dashboard sharing (link) | Yes | Yes | Yes | Yes |
| Scheduled email reports | Yes | Yes | Yes (Pro) | Yes |
| Embedded dashboards | Yes | Yes | Yes | Yes |
| Role-based access | Yes | Yes | Yes | Yes |
| Git-based versioning | No | No | No | No |
| Workspace collaboration | Yes (2026) | Yes | No | No |
| API access | Yes | Yes | Yes | Yes |

### 17.2 Annotation Collaboration Patterns

1. **In-visual comments** — tag colleagues, discuss specific data points
2. **Threaded discussions** — reply chains on dashboard elements
3. **@mentions** — notify specific team members
4. **Comment resolution** — mark discussions as resolved
5. **Activity feed** — timeline of changes and comments

### 17.3 Sharing Patterns

1. **Direct link** — URL to specific dashboard/view
2. **Embedded iframe** — dashboard embedded in other apps
3. **Scheduled report** — periodic email with PDF/image
4. **Export and share** — download then distribute
5. **Workspace** — shared environment for co-creation

### 17.4 BIAI Current: Single-user, no sharing
**Gap:** No collaboration features. Lower priority for local AI tool, but useful for team settings.

---

## 18. Recommendations for BIAI Evolution

Based on comprehensive analysis of the BI market, here are prioritized recommendations for BIAI evolution, grouped by impact and feasibility.

### Priority 1: High Impact, Moderate Effort

| Feature | Description | Reference |
|---------|-------------|-----------|
| **KPI Card Component** | Metric value + trend arrow + sparkline + period comparison | Section 13 |
| **Dashboard Grid Layout** | Configurable grid with tiled/floating widgets | Section 4 |
| **Expanded Chart Types** | Sankey (Plotly native), Treemap, Sunburst, Funnel, Gauge | Section 5 |
| **Cross-Filtering** | Click on chart element to filter other widgets | Section 14 |
| **Custom Color Palette** | Brand-aligned design tokens for consistent visualization | Section 15 |
| **Export: Excel + PDF** | Beyond current CSV; PDF for dashboards, Excel for data | Section 10 |

### Priority 2: High Impact, Higher Effort

| Feature | Description | Reference |
|---------|-------------|-----------|
| **Semantic Layer** | Business glossary mapping NL terms to SQL constructs | Section 8 |
| **Suggested Queries** | AI recommends follow-up questions based on results | Section 12 |
| **Anomaly Detection** | Automatic outlier/pattern detection in query results | Section 12 |
| **AI Narrative Summaries** | Auto-generated plain-language data explanations | Section 11 |
| **Conversation Memory** | Remember context across chat messages | Section 3 |
| **Process Mining Visualization** | Sankey + variant analysis from discovered processes | Section 6 |

### Priority 3: Medium Impact, Variable Effort

| Feature | Description | Reference |
|---------|-------------|-----------|
| **Interactive ERD Viewer** | React Flow based schema visualization | Section 7 |
| **Loading Animations** | Skeleton screens, smooth chart transitions | Section 16 |
| **Drill-Down Navigation** | Hierarchical data exploration (Year->Month->Day) | Section 14 |
| **BPMN/Swimlane Diagrams** | For process visualization (React Flow + swimlane plugin) | Section 6 |
| **Dashboard Templates** | Pre-built layouts for common use cases | Section 4 |
| **Annotation/Comments** | Add notes to data points or chart areas | Section 11, 17 |

### Priority 4: Future Considerations

| Feature | Description | Reference |
|---------|-------------|-----------|
| **Real-Time Streaming** | Live dashboard updates via WebSocket | Section 9 |
| **Collaborative Sharing** | Multi-user dashboard viewing/editing | Section 17 |
| **Agent-Based Queries** | Multi-step reasoning with tool use | Section 3, 8 |
| **Predictive Analytics** | Forecast and trend prediction | Section 12 |
| **BI-as-Code** | Git-based dashboard definitions | Section 2 |

### Technology Stack Alignment

| Current BIAI | Recommended Addition | Purpose |
|-------------|---------------------|---------|
| Plotly.js | (extend) | Sankey, Treemap, Sunburst, Gauge |
| React Flow | (already used) | Enhanced process visualization |
| Reflex | (extend) | Dashboard grid layout, cross-filtering |
| Vanna + Ollama | + semantic layer | Better NL2SQL accuracy |
| ChromaDB | (extend) | Conversation memory, query history |
| — | Design tokens (CSS vars) | Consistent color palette |
| — | jsPDF / xlsx.js | PDF and Excel export |

---

## Appendix A: Key Sources

### Commercial BI
- Gartner Peer Insights: Analytics and Business Intelligence Platforms (2026)
- ThoughtSpot Sage/Spotter documentation
- Power BI January 2026 Feature Summary
- Tableau Salt Design System

### Open Source BI
- Apache Superset vs Metabase comparison guides (2026)
- Holistics open-source BI tools overview
- Evidence.dev, Lightdash, Rill Data documentation

### AI-Native BI
- Ovaledge: AI-Driven Conversational Analytics Platforms (2026)
- Holistics: AI-Powered BI Tools Comparison Matrix (2026)
- Querio: Best Text-to-SQL Query Tools (2026)

### Process Mining
- Celonis Process Intelligence Platform documentation
- ICPM 2022: Visualization Libraries for Process Analytics
- bpmn-visualization library (Process Analytics)

### Design Systems
- IBM Carbon Design System: Data Visualization Color Palettes
- Google Material Design: Data Visualization Guidelines
- GitLab Pajamas: Data Visualization Color
- AWS Cloudscape: Data Vis Colors

### NL2SQL Research
- HKUSTDial NL2SQL Handbook (GitHub)
- Oracle Archer NL2SQL Challenge (2025)
- ACM Computing Surveys: LLM-based Text-to-SQL Systems (2025)

---

*End of Research Report*

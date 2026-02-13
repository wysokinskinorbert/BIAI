# Audyt: Dokumentacja vs Implementacja — BIAI

**Data:** 2026-02-13
**Zespół:** 5 agentów audytowych (docs-audit)
**Zakres:** 9 dokumentów z /docs vs cały codebase biai/

---

## 1. Podsumowanie Globalne

| Metryka | Wartość |
|---------|--------|
| Dokumentów przeanalizowanych | 9 |
| Wymagań/elementów sprawdzonych | 110+ |
| ✅ DONE (zaimplementowane) | ~78 (71%) |
| 🟡 PARTIAL (częściowo) | ~17 (15%) |
| ❌ MISSING (brakuje) | ~15 (14%) |
| Plików w mapie codebase | 45 (docs) vs 68 (aktualnie) |
| Nowych plików nie opisanych w docs | 23 |

**Ogólna ocena:** Rdzeń aplikacji jest solidnie zaimplementowany i w wielu obszarach **przekracza** dokumentację (np. Dynamic Process Discovery, DynamicStyler, React Flow custom nodes). Implementacja poszła inną, często lepszą drogą niż pierwotny plan (post-hoc process detection zamiast AgentRouter, React Flow zamiast Mermaid.js). Główne braki: tryb demo, ECharts, testy integracyjne, rendering 3 typów wykresów.

---

## 2. Audyt poc.md + architecture.md (Agent: auditor-poc)

### Stack technologiczny

| Element z PoC | Status | Implementacja |
|---------------|--------|---------------|
| Streamlit → **Reflex** | ✅ DONE | Świadoma decyzja — Reflex 0.8.x |
| ECharts (animowane wykresy) | ❌ MISSING | Tylko Plotly. Zero referencji do ECharts w kodzie |
| Plotly (wykresy biznesowe) | ✅ DONE | `chart_card.py` → `rx.plotly()`, 6 typów |
| Mermaid.js (diagramy ERD) | ❌ MISSING | Zero referencji. React Flow pokrywa procesy |
| Graphviz | ❌ MISSING | Zero referencji |
| python-oracledb (thin mode) | ✅ DONE | `db/oracle.py` — thin mode |
| asyncpg (PostgreSQL) | ✅ DONE | `db/postgresql.py` |
| Ollama (local LLM) | ✅ DONE | Vanna + httpx streaming |
| Vanna.ai (RAG Text-to-SQL) | ✅ DONE | `ai/vanna_client.py`, ChromaDB |
| pandas | ✅ DONE | Cały pipeline |
| sqlglot | ✅ DONE | `sql_validator.py` — AST + transpilation |
| pydantic-settings | ✅ DONE | `config/settings.py` z `.env` support |
| Docker Compose | ✅ DONE | `docker-compose.dev.yml` |
| ChromaDB | ✅ DONE | Kolekcje: documentation, ddl, sql |

### Architektura i przepływ danych

| Wymaganie | Status | Uwagi |
|-----------|--------|-------|
| Abstract DatabaseConnector (ABC) | ✅ DONE | `db/base.py:15` — connect/disconnect/execute_query/get_tables/get_schema_snapshot |
| OracleConnector | ✅ DONE | `db/oracle.py:16` |
| PostgreSQLConnector | ✅ DONE | `db/postgresql.py:16` |
| Schema Retrieval | ✅ DONE | `SchemaManager` z cache TTL (300s) |
| RAG Retrieval → ChromaDB | ✅ DONE | `training.py` trains DDL/docs/examples |
| SQL Generation | ✅ DONE | `SelfCorrectionLoop` → `vanna.generate_sql()` |
| SQL Validation (4 layers) | ✅ DONE | keywords → patterns → AST → transpilation |
| Self-correction (max retries) | ✅ DONE | MAX_RETRIES=5, error feedback loop |
| Execute → DataFrame | ✅ DONE | `QueryExecutor` z timeout i row limit |
| Chart Selection | ✅ DONE | `ChartAdvisor` heuristic + LLM fallback |
| Description Streaming | ✅ DONE | httpx async streaming z Ollama API |
| 5 warstw architektury | ✅ DONE | UI → State → AI → Data → Infrastructure |
| LLM routing: SQL vs Diagram | ❌ MISSING | Pipeline ZAWSZE generuje SQL. Procesy wykrywane post-hoc |

### UI

| Wymaganie | Status | Uwagi |
|-----------|--------|-------|
| Split-screen (Chat 40% + Dashboard 60%) | ✅ DONE | `layout.py:38-53` |
| Sidebar z konfiguracją połączenia | ✅ DONE | `connection_form.py` — Host, Port, DB, User, Pass |
| Przycisk "Połącz i Pobierz Schemat" | ✅ DONE | Auto-refresh schema po połączeniu |
| Wybór modelu Ollama z listy | ✅ DONE | `model_selector.py` — refresh z `/api/tags` |
| Dymki czatu (User vs AI) | ✅ DONE | `chat_message.py` — avatary, kolory, direction |
| Historia rozmowy | ✅ DONE | `ChatState.messages` |
| Dashboard: karta z wykresem | ✅ DONE | `chart_card.py` |
| Dashboard: tabele danych | ✅ DONE | `data_table.py` |
| Dashboard: diagramy Mermaid | ❌ MISSING | React Flow zamiast Mermaid |
| Opcja powiększenia wykresu | ❌ MISSING | Brak fullscreen/enlarge UI |
| Dark Mode | ✅ DONE | `appearance="inherit"`, `plotly_dark` |
| Schema Explorer | ✅ DONE | `schema_explorer.py` |

### Bezpieczeństwo (4 warstwy)

| Warstwa | Status |
|---------|--------|
| 1. sqlglot AST → only SELECT | ✅ DONE — `isinstance(statement, exp.Select)` + walk for nested |
| 2. Regex → blocked keywords (17 słów) | ✅ DONE — `_check_blocked_keywords()` |
| 3. Single statement → block `;` | ✅ DONE — `_check_blocked_patterns()` |
| 4. Read-only DB user | 🟡 PARTIAL — nie wymuszane w kodzie, zależy od konfiguracji |

### Tryb Demo

| Wymaganie | Status |
|-----------|--------|
| Mock data gdy brak połączenia z bazą | ❌ MISSING — komunikat "Nie jesteś połączony" zamiast demo |

**Statystyki agenta: 33 DONE, 2 PARTIAL, 7 MISSING**

---

## 3. Audyt analysis_poc_gaps.md + analysis_codebase_map.md (Agent: auditor-gaps)

### Luki z analizy PoC — status naprawy

| Luka | Status docs | Aktualny status | Uwagi |
|------|------------|-----------------|-------|
| Brak PostgreSQL connector | NOT_IMPL | ✅ FIXED | `db/postgresql.py` pełna impl |
| Brak walidacji SQL | NOT_IMPL | ✅ FIXED | 4-warstwowy `SQLValidator` |
| Brak self-correction loop | NOT_IMPL | ✅ FIXED | `SelfCorrectionLoop` max 5 retry |
| Brak dialect-specific SQL | NOT_IMPL | ✅ FIXED | `DialectHelper` + sqlglot transpilation |
| Brak schema training (Vanna) | NOT_IMPL | ✅ FIXED | `SchemaTrainer` + lazy training |
| Brak error handling | NOT_IMPL | ✅ FIXED | try/except na każdym etapie |
| Brak connection presets | NOT_IMPL | ✅ FIXED | `connection_presets.py`, `presets.py` |
| Brak CSV export | NOT_IMPL | ✅ FIXED | `QueryState.csv_data` + `rx.download()` |
| Brak streaming AI | NOT_IMPL | ✅ FIXED | httpx async streaming |
| Agent Routing (SQL vs Diagram) | NOT_IMPL | ✅ FIXED (inaczej) | Post-hoc detection zamiast pre-routing |
| Ścieżka generowania diagramów | NOT_IMPL | ✅ FIXED | React Flow + ProcessGraphBuilder |
| Dashboard: diagramy renderowane | NOT_IMPL | ✅ FIXED | `process_flow_card()` w dashboardzie |
| pydantic-settings | PARTIAL | ✅ FIXED | Pełna impl z `BaseSettings` + `.env` |
| Fullscreen/zoom wykresu | NOT_IMPL | 🟡 PARTIAL | React Flow ma zoom, Plotly nie ma fullscreen |
| Mermaid.js/Graphviz | NOT_IMPL | 🟡 PARTIAL | React Flow zastępuje, ale inna technologia |
| Testy jednostkowe | NOT_IMPL | 🟡 PARTIAL | 7 plików testów, ~40% pokrycia |
| ECharts (animowane wykresy) | NOT_IMPL | ❌ STILL MISSING | Zero implementacji |
| ECharts: Dark Mode, glow | NOT_IMPL | ❌ STILL MISSING | j.w. |
| Tryb Demo z mock data | NOT_IMPL | ❌ STILL MISSING | Zero implementacji |
| MongoDB connector | NOT_IMPL | ❌ STILL MISSING | Nie planowane w MVP |
| Docker CI/CD | PARTIAL | ❌ STILL MISSING | Brak `.github/workflows/` |

### Mapa codebase — rozbieżności

**Docs:** 45 plików → **Aktualnie:** 68 plików (+23 nowych, głównie process visualization + testy)

| Warstwa | Docs | Aktualnie | Nowe pliki |
|---------|------|-----------|------------|
| AI Layer | 7 | 14 | +7 (process_*) |
| Components | 10 | 14 | +4 (react_flow/, process_map_card) |
| State | 8 | 10 | +2 (process.py, process_map.py) |
| Models | 5 | 7 | +2 (process.py, discovery.py) |
| Testy | 0 | 7 | +7 (cały katalog tests/) |
| DB/Config/Utils/Pages | bez zmian | bez zmian | 0 |

### Uwagi z mapy — weryfikacja

| Uwaga | Status |
|-------|--------|
| "Brak testów" | ✅ NAPRAWIONE — 7 plików testów |
| "Brak CI/CD" | ❌ STILL MISSING |
| "`_build_plotly_figure()` powinna być w osobnym module" | ❌ STILL MISSING — nadal w `chat.py` |
| "`ChatState.messages` to `list[dict]` zamiast typed model" | 🟡 Bez zmian |
| "`model_selector.py` łączy State + Component" | 🟡 Bez zmian |

---

## 4. Audyt architecture_process_visualization.md (Agent: auditor-process-viz)

### Kluczowa zmiana architekturalna

Dokumentacja opisywała **2-ścieżkowy routing** (`AgentRouter` → SQL_QUERY vs PROCESS_DIAGRAM vs HYBRID).
Implementacja zastosowała **post-hoc detection**: KAŻDE pytanie → standardowy pipeline SQL → wynik analizowany przez `ProcessDetector`. Jeśli DataFrame zawiera dane procesowe → budowany graf React Flow.

**Implikacja:** `AgentRouter`, `ROUTER_PROMPT`, `PROCESS_SQL_PROMPT` nie istnieją i **nie są potrzebne** w aktualnej architekturze.

### Komponenty

| Komponent z docs | Status | Uwagi |
|------------------|--------|-------|
| AgentRouter | ❌ MISSING (celowo) | Zastąpiony post-hoc detection |
| ROUTER_PROMPT | ❌ MISSING (celowo) | Niepotrzebny |
| PROCESS_SQL_PROMPT | ❌ MISSING (celowo) | Niepotrzebny |
| ProcessDetector | ✅ DONE | Inna impl niż w docs (heurystyki DataFrame) |
| ProcessTransformer → **ProcessGraphBuilder** | ✅ DONE | Zmieniona nazwa i podejście |
| calculate_layout | ✅ DONE | Kahn's topological sort, TB+LR |
| ProcessState | ✅ DONE | flow_nodes, flow_edges, bottleneck, metrics |
| React Flow wrapper | ✅ DONE | @xyflow/react@12.9.0, NoSSRComponent |
| process_flow_card | ✅ DONE | Header + canvas 400px + metrics bar |
| CSS glow effects | ✅ DONE | global.css + process-flow.css |
| Dashboard integracja | ✅ DONE | `process_flow_card()` w layout |
| Chat badge "Process" | ✅ DONE | `has_process` w message |
| ChartType.PROCESS_FLOW | ✅ DONE | W models/chart.py |

### Node Types (wszystkie z docs + 1 extra)

| Typ | Custom JS Node | Status |
|-----|---------------|--------|
| processStart | ProcessStartNode (zielony okrągły) | ✅ DONE |
| processEnd | ProcessEndNode (czerwony okrągły) | ✅ DONE |
| processTask | ProcessTaskNode (prostokątny z metrykami) | ✅ DONE |
| processGateway | ProcessGatewayNode (diamentowy) | ✅ DONE |
| processCurrent | ProcessCurrentNode (pulsujący) | ✅ DONE (extra) |

### Edge Types

| Typ | Status |
|-----|--------|
| smoothstep + animated | ✅ DONE — `ProcessEdgeType.ANIMATED` |
| color-coded edges | ✅ DONE — `_get_edge_style()` |
| DIMMED (przerywana linia) | ✅ DONE (extra) |
| NORMAL | ✅ DONE (extra) |

### Layout Algorithm

| Aspekt | Status |
|--------|--------|
| Kahn's topological sort | ✅ DONE — identyczne parametry |
| node_width=180, node_height=60, rank_sep=80, node_sep=40 | ✅ DONE |
| TB + LR directions | ✅ DONE |
| Cycle handling | ✅ DONE — unvisited → last layer |
| toggle_layout() | ✅ DONE |

### React Flow Integration

| Aspekt | Status |
|--------|--------|
| @xyflow/react@12.9.0 | ✅ DONE |
| NoSSRComponent wrapper | ✅ DONE |
| Background (dots, gap=20) | ✅ DONE |
| Controls (zoom, fit_view) | ✅ DONE |
| MiniMap (color-mode aware) | ✅ DONE |
| ReactFlowProvider | ✅ DONE |
| Custom CSS import | ✅ DONE |
| nodeTypes JS registration | ✅ DONE |
| color_mode dark/light | ✅ DONE — lepsze niż docs (responsive) |

### Styling — DynamicStyler (ULEPSZONY vs docs)

Docs opisywały hardcoded `STATUS_COLORS` i `STATUS_ICONS` mapy. Implementacja zastąpiła je **algorytmicznym `DynamicStyler`**:
- 9 kategorii semantycznych (success, error, warning, info, review, start, neutral, transition, reopen)
- 60+ słów kluczowych
- 3 poziomy priorytetów (AI suggestion → semantic match → hash fallback)
- Deterministyczny `_hash_color()` z MD5

### Bottleneck Detection

| Aspekt | Status |
|--------|--------|
| Wykrywanie (longest duration) | ✅ DONE — `max(state_durations)` |
| `is_bottleneck=True` + glow CSS | ✅ DONE — pulsujący CSS |
| `bottleneck_label` w metrics | ✅ DONE — alert-triangle icon + red text |

### Process Types (4 + dynamic)

| Typ | Status |
|-----|--------|
| Order Fulfillment | ✅ DONE |
| Sales Pipeline | ✅ DONE |
| Support Tickets | ✅ DONE |
| Approval Workflow | ✅ DONE |
| Dynamic (auto-discovery) | ✅ DONE (extra — ProcessDiscoveryEngine) |

### Dodatkowe komponenty (nie w docs, ale zaimplementowane)

| Komponent | Opis |
|-----------|------|
| ProcessDiscoveryEngine | Auto-discovery procesów z schema/danych |
| ProcessDiscoveryCache | TTL cache (moduł-level singleton) |
| DynamicStyler | Algorytmiczne kolory/ikony |
| DynamicProcessTrainer | Dynamiczne dane treningowe |
| process_training.py | Hardcoded training data dla 4 procesów |
| ProcessMapState + process_map_card | UI discovery na dashboardzie |
| models/discovery.py | DiscoveredProcess, ColumnCandidate, etc. |
| PROCESS_DISCOVERY_PROMPT | AI-enrichment odkrytych procesów |

**Agent: 30 DONE (+ 10 extra), 2 PARTIAL, 3 MISSING (celowo — inna architektura)**

---

## 5. Audyt analysis_viz_technologies.md + analysis_test_data.md (Agent: auditor-viz-tests)

### Technologie wizualizacji — rekomendacja vs implementacja

| Technologia | Rekomendacja | Status | Uwagi |
|-------------|-------------|--------|-------|
| React Flow (@xyflow/react) | GŁÓWNA (procesy) | ✅ DONE | Pełna impl z custom nodes, ~85% zgodność |
| Plotly | Wykresy biznesowe | ✅ DONE | 6 typów renderowanych |
| Mermaid.js | Opcjonalne (statyczne) | ❌ MISSING | Celowo pominięte |
| ECharts | Nie rekomendowane | ❌ MISSING | Zgodne z rekomendacją tego dokumentu |
| BPMN.js / D3.js / Cytoscape / GoJS | Nie rekomendowane | ❌ MISSING | Zgodne z rekomendacją |

### Typy wykresów

| Typ | Rendering | ChartAdvisor logic | Status |
|-----|-----------|-------------------|--------|
| BAR | ✅ | ✅ heurystyka + LLM | ✅ DONE |
| LINE | ✅ | ✅ time series detection | ✅ DONE |
| PIE | ✅ | ✅ proportion keywords | ✅ DONE |
| SCATTER | ✅ | ✅ correlation detection | ✅ DONE |
| AREA | ✅ | ❌ brak logiki w advisor | 🟡 PARTIAL |
| TABLE | ✅ | ✅ fallback | ✅ DONE |
| PROCESS_FLOW | ✅ (React Flow) | ✅ ProcessDetector | ✅ DONE |
| HEATMAP | ❌ brak renderingu | ❌ brak logiki | 🟡 PARTIAL (tylko enum) |
| TIMELINE | ❌ brak renderingu | ❌ brak logiki | 🟡 PARTIAL (tylko enum) |
| SANKEY | ❌ brak renderingu | ❌ brak logiki | 🟡 PARTIAL (tylko enum) |

### Dane testowe — 4 zestawy procesowe

| Zestaw | Oracle seed | PG seed | Tabele | Status |
|--------|-----------|---------|--------|--------|
| Order Fulfillment | ✅ ~500 rows | ✅ | ORDER_PROCESS_LOG + view | ✅ DONE |
| Sales Pipeline | ✅ 300 deals | ✅ | SALES_PIPELINE + PIPELINE_HISTORY | ✅ DONE |
| Support Tickets | ✅ | ✅ | SUPPORT_TICKETS + TICKET_HISTORY | ✅ DONE |
| Approval Workflow | ✅ | ✅ | APPROVAL_REQUESTS + APPROVAL_STEPS | ✅ DONE |

### Infrastruktura testowa

| Element | Status | Uwagi |
|---------|--------|-------|
| docker-compose.dev.yml (PG + Oracle) | ✅ DONE | PG:5433, Oracle:1521 |
| Healthchecks | ✅ DONE | pg_isready, healthcheck.sh |
| Basic seeds w Docker volumes | ✅ DONE | Auto-init |
| Process seeds w Docker volumes | ❌ MISSING | Trzeba uruchomić ręcznie! |
| oracle-process-fix.sql | ✅ DONE | Fix ORA-06532 VARRAY edge case |
| Views analityczne | 🟡 PARTIAL | Oracle OK, PostgreSQL niepewne |

### Testy

| Element | Status |
|---------|--------|
| test_sql_validator.py | ✅ DONE |
| test_self_correction.py | ✅ DONE |
| test_pipeline.py | ✅ DONE |
| test_discovery.py (28 testów) | ✅ DONE |
| test_process.py (~25 testów) | ✅ DONE |
| conftest.py (fixtures) | ✅ DONE |
| Integration tests z Docker DB | ❌ MISSING |
| Testy 30 przykładowych pytań AI | ❌ MISSING |
| Performance benchmarks | ❌ MISSING |

---

## 6. Audyt plan_dynamic_process_discovery.md + implementation_report.md (Agent: auditor-discovery)

### Dynamic Process Discovery — realizacja planu

| Element planu | Status | Uwagi |
|---------------|--------|-------|
| ProcessDiscoveryEngine | ✅ DONE | `ai/process_discovery.py` — 7-krokowy pipeline |
| Heurystyka: status columns | ✅ DONE | Detekcja kolumn ze statusami |
| Heurystyka: timestamp sequences | ✅ DONE | Detekcja sekwencji czasowych |
| Heurystyka: FK chains | ✅ DONE | Śledzenie łańcuchów kluczy obcych |
| LLM-enhanced interpretation | ✅ DONE | PROCESS_DISCOVERY_PROMPT |
| ProcessDiscoveryCache | ✅ DONE | Moduł-level singleton z TTL (600s) |
| DynamicProcessTrainer | ✅ DONE | Generacja docs + examples z DiscoveredProcess |
| Integration z AIPipeline.train_schema() | ✅ DONE | Cache check → discover → train |
| Integration z AIPipeline.process() | ✅ DONE | Step 3b: detection + graph building |
| Config constants (USE_DYNAMIC_DISCOVERY, DISCOVERY_*) | ✅ DONE | constants.py |
| Fallback do legacy training | ✅ DONE | `has_process_tables()` check |

### Implementation Report — aktualność

| Element raportu | Status |
|-----------------|--------|
| Core pipeline (SQL gen → execute → chart) | ✅ Aktualny |
| 4-layer SQL security | ✅ Aktualny |
| Self-correction loop (MAX_RETRIES=5) | ✅ Aktualny |
| Dialect transpilation (LIMIT→FETCH FIRST) | ✅ Aktualny |
| Oracle bind variable fix | ✅ Aktualny |
| Process visualization | ✅ Aktualny |
| Dynamic discovery | ✅ Aktualny |
| Reflex state patterns | ✅ Aktualny |
| Znane ograniczenia | ⚠️ Do weryfikacji — niektóre mogły zostać naprawione |

---

## 7. Plan Kolejnych Kroków

### Priorytet WYSOKI

| # | Zadanie | Opis | Złożoność | Źródło wymagania |
|---|---------|------|-----------|-----------------|
| 1 | **Tryb Demo** | Mock data/demo mode gdy brak DB — PoC wymaga explicite | MEDIUM | poc.md §5 |
| 2 | **Process seeds w Docker auto-init** | Dodaj process-seed.sql do volumes w docker-compose.dev.yml | LOW | analysis_test_data.md |
| 3 | **Integration tests z Docker DB** | E2E: compose up → connect → query → verify | HIGH | analysis_test_data.md |
| 4 | **Rendering HEATMAP/TIMELINE/SANKEY** | ChartType enum istnieje ale brak logiki w `_build_plotly_figure()` i `ChartAdvisor` | MEDIUM | analysis_viz_technologies.md |

### Priorytet ŚREDNI

| # | Zadanie | Opis | Złożoność | Źródło |
|---|---------|------|-----------|--------|
| 5 | **Aktualizacja analysis_codebase_map.md** | +23 nowe pliki do opisania, zaktualizować graf zależności | LOW | auditor-gaps |
| 6 | **Wynieś `_build_plotly_figure()` z chat.py** | Do osobnego modułu (zalecenie z codebase map) | LOW | analysis_codebase_map.md |
| 7 | **Diagramy ERD** | Wizualizacja relacji tabel z SchemaSnapshot (React Flow lub Mermaid) | MEDIUM | poc.md |
| 8 | **Export process map do PNG/SVG** | Przycisk export w process_flow_card | LOW | architecture_process_visualization.md |
| 9 | **Pokrycie testami do 70%+** | Brakuje: chart_advisor, schema_manager, query_executor, connectors | HIGH | analysis_poc_gaps.md |
| 10 | **Read-only DB user warning** | Informacja w UI gdy user może mieć uprawnienia write | LOW | architecture.md |
| 11 | **Fullscreen wykresu** | Powiększanie kart Plotly do fullscreen/modal | LOW | poc.md |

### Priorytet NISKI (nice-to-have)

| # | Zadanie | Opis | Złożoność |
|---|---------|------|-----------|
| 12 | **Process comparison view** | Side-by-side porównanie procesów | HIGH |
| 13 | **Process animation** | Token animation w React Flow | MEDIUM |
| 14 | **ECharts** | Animowane wykresy obok Plotly (oryginalny PoC) | HIGH |
| 15 | **Mermaid.js** | Diagramy sekwencji (opcjonalne wg viz analysis) | MEDIUM |
| 16 | **CI/CD** | GitHub Actions workflows | MEDIUM |
| 17 | **Performance benchmarks** | Pomiar czasu SQL gen, execution, chart rendering | MEDIUM |
| 18 | **MongoDB connector** | Rozszerzenie na NoSQL (przyszłość) | HIGH |
| 19 | **Testy 30 przykładowych pytań AI** | Scenariusze z analysis_test_data.md | MEDIUM |

---

## 8. Macierz Dokumentacja vs Kod

| Dokument | Pokrycie | Kluczowe braki |
|----------|----------|----------------|
| `poc.md` | **78%** | Tryb demo, ECharts, Mermaid.js, fullscreen wykresów |
| `architecture.md` | **95%** | Tylko read-only user enforcement |
| `analysis_poc_gaps.md` | **85%** | ECharts, tryb demo, CI/CD |
| `analysis_codebase_map.md` | **65%** | 23 nowe pliki, zmieniony graf zależności |
| `architecture_process_visualization.md` | **90%** | AgentRouter (celowo inaczej), export, animation |
| `analysis_viz_technologies.md` | **85%** | Mermaid.js (opcjonalne), AREA/HEATMAP/TIMELINE/SANKEY |
| `analysis_test_data.md` | **75%** | Process seeds w auto-init, integration tests, pytania AI |
| `plan_dynamic_process_discovery.md` | **95%** | Plan prawie w pełni zrealizowany |
| `implementation_report.md` | **90%** | Aktualny, drobne zmiany |

**Średnie pokrycie: ~84%**

---

## 9. Kluczowe Obserwacje

### Implementacja PRZEKRACZA dokumentację w:
1. **Dynamic Process Discovery** — cały moduł nie opisany w większości docs
2. **DynamicStyler** — algorytmiczne kolory/ikony zamiast hardcoded map
3. **5 typów custom React Flow nodes** — docs opisywały 4
4. **Color-mode aware UI** — responsive dark/light zamiast hardcoded dark
5. **ProcessDiscoveryCache** — TTL cache na poziomie modułu
6. **Connection presets** — zapisywanie ulubionych połączeń
7. **Encryption utilities** — crypto.py dla bezpiecznego storage

### Świadome zmiany architekturalne:
1. **Streamlit → Reflex** — lepszy framework SPA
2. **Mermaid.js/Graphviz → React Flow** — lepsza interaktywność
3. **AgentRouter → Post-hoc ProcessDetector** — prostsze, mniej error-prone
4. **Hardcoded styles → DynamicStyler** — skalowalne, semantyczne
5. **Bezpośrednie prompty → Vanna RAG** — lepsza dokładność SQL

### Elementy wymagające pilnej aktualizacji docs:
1. `analysis_codebase_map.md` — najbardziej nieaktualny (65% pokrycia)
2. `architecture_process_visualization.md` — inna architektura niż opisana (post-hoc vs routing)

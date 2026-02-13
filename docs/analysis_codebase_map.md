# BIAI - Mapa Komponentow i Audyt Kodu

> Data audytu: 2026-02-13
> Wersja: Reflex 0.8.x, Vanna.ai, Ollama, asyncpg, oracledb

---

## 1. Architektura Ogolna

```
biai/
  biai.py              # Entry point - Reflex App
  config/              # Konfiguracja (pydantic-settings, stale)
  models/              # Pydantic modele danych
  db/                  # Warstwa bazy danych (ABC + Oracle/PostgreSQL)
  ai/                  # Warstwa AI (Vanna + pipeline)
  state/               # Reflex State (reaktywny stan frontendu)
  components/          # Reflex UI Components
  pages/               # Strony (index, settings)
  utils/               # Narzedzia (logger, crypto, storage)
```

**Architektura:** 3-warstwowa (DB -> AI -> UI) z Reflex state jako warstwa posrednia.

**Flow glowny:**
```
User Question -> ChatState.process_message()
  -> AIPipeline.process(question)
    -> SelfCorrectionLoop.generate_with_correction()
      -> Vanna.generate_sql() + SQLValidator.validate()
    -> QueryExecutor.execute(sql)
    -> ChartAdvisor.recommend(df)
  -> QueryState.set_query_result()
  -> ChartState.set_plotly()
  -> stream generate_description() -> ChatState messages
```

---

## 2. Mapa Modulow - Szczegoly

### 2.1 AI Layer (`biai/ai/`)

#### `__init__.py`
- **Co robi:** Pusty init
- **Stan:** STUB (plik istnieje ale pusty)
- **Zaleznosci:** brak

#### `pipeline.py` (AIPipeline)
- **Co robi:** Orkiestrator calego flow: question -> SQL -> validate -> execute -> chart -> description
- **Stan:** KOMPLETNY
- **Kluczowe klasy:** `AIPipeline`, `PipelineResult`
- **Metody:** `train_schema()`, `process(question)`, `generate_description(question, sql, df)`
- **Zaleznosci:** vanna_client, sql_validator, self_correction, chart_advisor, training, prompt_templates, db.base, db.dialect, db.schema_manager, db.query_executor, models.connection/chart/query
- **Punkt rozszerzenia:** `process()` zwraca `PipelineResult` - mozna dodac nowe pola (np. `process_visualization`, `business_process_data`). Metoda `generate_description()` jest streamowana - analogicznie mozna stworzyc `generate_process_description()`.

#### `vanna_client.py` (MyVanna)
- **Co robi:** Klient Vanna.ai laczacy ChromaDB (vectorstore) + Ollama (LLM)
- **Stan:** KOMPLETNY
- **Kluczowe klasy:** `MyVanna(ChromaDB_VectorStore, Ollama)`, factory `create_vanna_client()`
- **Metody:** `reset_collections()` (fix dla corrupted HNSW)
- **Zaleznosci:** vanna.chromadb, vanna.ollama, config.constants
- **Punkt rozszerzenia:** Mozna dodac custom `generate_sql()` override dla process-aware queries.

#### `chart_advisor.py` (ChartAdvisor)
- **Co robi:** Rekomenduje typ wykresu (heurystyka + LLM fallback)
- **Stan:** KOMPLETNY
- **Kluczowe klasy:** `ChartAdvisor`
- **Metody:** `recommend(question, sql, df)`, `_heuristic_recommend()`, `_llm_recommend()`
- **Typy wykresow:** BAR, LINE, PIE, SCATTER, AREA, TABLE
- **Zaleznosci:** models.chart, prompt_templates
- **Punkt rozszerzenia:** Mozna dodac `ChartType.PROCESS_FLOW` / `ChartType.GANTT` / `ChartType.SANKEY` i odpowiednie heurystyki wykrywania procesow biznesowych.

#### `self_correction.py` (SelfCorrectionLoop)
- **Co robi:** Generuje SQL z auto-korekcja (max N prob) - obsluguje refusal, validation errors, execution errors
- **Stan:** KOMPLETNY
- **Kluczowe klasy:** `SelfCorrectionLoop`
- **Metody:** `generate_with_correction(question, db_executor)`
- **Zaleznosci:** sql_validator, prompt_templates, models.query
- **Punkt rozszerzenia:** Mozna dodac callback `on_attempt(attempt, sql, error)` do monitorowania procesu.

#### `sql_validator.py` (SQLValidator)
- **Co robi:** 3-warstwowa walidacja SQL (blocked keywords -> regex patterns -> AST sqlglot) + transpilacja dialektow
- **Stan:** KOMPLETNY
- **Kluczowe klasy:** `SQLValidator`
- **Metody:** `validate(sql)`, `_sanitize_bind_variables(sql)` (Oracle fix)
- **Zaleznosci:** sqlglot, config.constants (BLOCKED_KEYWORDS, BLOCKED_PATTERNS)
- **Punkt rozszerzenia:** Mozna dodac whitelist tabel procesowych lub specjalne reguły walidacji dla process-related queries.

#### `prompt_templates.py`
- **Co robi:** Szablony promptow: SYSTEM_PROMPT, CORRECTION_PROMPT, CHART_ADVISOR_PROMPT, DESCRIPTION_PROMPT
- **Stan:** KOMPLETNY
- **Zaleznosci:** brak
- **Punkt rozszerzenia:** Mozna dodac PROCESS_DETECTION_PROMPT, PROCESS_DESCRIPTION_PROMPT do identyfikacji i opisu procesow biznesowych w danych.

#### `training.py` (SchemaTrainer)
- **Co robi:** Trenuje Vanna z DDL, dokumentacja, przyklady query
- **Stan:** KOMPLETNY
- **Kluczowe klasy:** `SchemaTrainer`
- **Metody:** `train_ddl()`, `train_documentation()`, `train_examples()`, `train_full()`, `get_training_data()`, `remove_training_data()`
- **Zaleznosci:** models.schema
- **Punkt rozszerzenia:** Mozna dodac `train_process_knowledge()` do nauczenia Vanna o procesach biznesowych (np. "pokaz przebieg procesu zamowienia X").

#### `process_detector.py` (ProcessDetector)
- **Co robi:** Heurystyczna detekcja danych procesowych w DataFrame — rozpoznaje kolumny transition (from/to), status/stage, keywords w SQL
- **Stan:** KOMPLETNY
- **Kluczowe klasy:** `ProcessDetector`
- **Metody:** `detect(df, sql)`, `is_process_question(question)`, `detect_process_type(df, sql)`
- **Zaleznosci:** pandas, models.process

#### `process_discovery.py` (ProcessDiscoveryEngine)
- **Co robi:** 7-krokowy pipeline auto-discovery procesow biznesowych z schema i danych DB — wykrywa status columns, timestamps, FK chains + wzbogacanie LLM
- **Stan:** KOMPLETNY
- **Kluczowe klasy:** `ProcessDiscoveryEngine`
- **Metody:** `discover(connector, schema, vanna_client)` — zwraca `list[DiscoveredProcess]`
- **Zaleznosci:** models.discovery, db.base, db.schema_manager

#### `process_graph_builder.py` (ProcessGraphBuilder)
- **Co robi:** Buduje `ProcessFlowConfig` z DataFrame — tworzy nodes/edges z transitions, aggregates lub known sequences; wykrywa bottleneck
- **Stan:** KOMPLETNY (313 LOC)
- **Kluczowe klasy:** `ProcessGraphBuilder`
- **Metody:** `build(df, process_type, sql)` — zwraca `ProcessFlowConfig | None`
- **Zaleznosci:** pandas, models.process

#### `process_cache.py` (ProcessDiscoveryCache)
- **Co robi:** Modul-level TTL cache dla wynikow discovery (DISCOVERY_CACHE_TTL=600s) — unika powtarzania kosztownych skanow schema/DB
- **Stan:** KOMPLETNY
- **Kluczowe klasy:** `ProcessDiscoveryCache`
- **Metody:** `get(key)`, `set(key, value)`, `invalidate(key)`, `clear()`
- **Zaleznosci:** brak (standalone)

#### `process_training.py`
- **Co robi:** Statyczne dane treningowe Vanna dla 4 typow procesow (order fulfillment, sales pipeline, support ticket, approval workflow) — przyklady SQL + dokumentacja
- **Stan:** KOMPLETNY
- **Kluczowe:** `PROCESS_TRAINING_DATA: dict` z kluczami per process type
- **Zaleznosci:** brak

#### `process_training_dynamic.py` (DynamicProcessTrainer)
- **Co robi:** Generuje dynamiczne docs + examples z `DiscoveredProcess` dla Vanna training — buduje DDL, documentation i sample queries
- **Stan:** KOMPLETNY
- **Kluczowe klasy:** `DynamicProcessTrainer`
- **Metody:** `generate_training(discovered_processes)` — zwraca training items
- **Zaleznosci:** models.discovery

#### `dynamic_styler.py` (DynamicStyler)
- **Co robi:** Algorytmiczne przypisywanie kolorow i ikon dla statusow — 9 kategorii semantycznych, 60+ keywords, hash-based fallback dla nierozpoznanych statusow
- **Stan:** KOMPLETNY
- **Kluczowe klasy:** `DynamicStyler`
- **Metody:** `get_color(status)`, `get_icon(status)`, `style_node(status)`
- **Zaleznosci:** brak (standalone)

#### `process_layout.py`
- **Co robi:** Oblicza pozycje node'ow za pomoca topological sort (Kahn's algorithm) — wspiera kierunki TB (top-bottom) i LR (left-right)
- **Stan:** KOMPLETNY (68 LOC)
- **Kluczowe:** `calculate_layout(nodes, edges, direction, node_width=180, rank_sep=80)`
- **Zaleznosci:** brak (standalone, pure algorithm)

---

### 2.2 DB Layer (`biai/db/`)

#### `__init__.py`
- **Stan:** STUB (pusty)

#### `base.py` (DatabaseConnector ABC)
- **Co robi:** Abstrakcyjna klasa bazowa definiujaca interfejs konektora
- **Stan:** KOMPLETNY
- **Metody abstrakcyjne:** `connect()`, `disconnect()`, `test_connection()`, `execute_query()`, `get_tables()`, `get_schema_snapshot()`, `get_server_version()`
- **Zaleznosci:** models.connection, models.schema
- **Punkt rozszerzenia:** Interfejs jest stabilny. Nowe konektory (MySQL, SQLite) moga go implementowac.

#### `oracle.py` (OracleConnector)
- **Co robi:** Oracle connector z connection pooling (oracledb thin mode)
- **Stan:** KOMPLETNY
- **Kluczowe:** Pool min=1/max=4, PK/FK detection, `asyncio.to_thread()` wrapper dla synchronicznego oracledb
- **Zaleznosci:** oracledb, models.connection/schema
- **Punkt rozszerzenia:** Mozna dodac `get_process_tables()` ktory wykrywa tabele z kolumnami statusowymi, datami etapow itp.

#### `postgresql.py` (PostgreSQLConnector)
- **Co robi:** PostgreSQL connector z asyncpg (natywny async)
- **Stan:** KOMPLETNY
- **Kluczowe:** Pool min=1/max=4, PK/FK detection, `if not schema: schema = "public"` guard
- **Zaleznosci:** asyncpg, models.connection/schema

#### `schema_manager.py` (SchemaManager)
- **Co robi:** Cache'owany manager schema (TTL-based, domyslnie 5min)
- **Stan:** KOMPLETNY
- **Metody:** `get_snapshot()`, `get_tables()`, `get_ddl_statements()`, `get_table_names()`, `invalidate_cache()`
- **Zaleznosci:** db.base, models.schema, config.constants

#### `query_executor.py` (QueryExecutor)
- **Co robi:** Wykonuje SQL z timeoutem i limitem wierszy
- **Stan:** KOMPLETNY
- **Kluczowe:** timeout=30s, row_limit=10000, zwraca `QueryResult | QueryError`
- **Zaleznosci:** db.base, models.query, config.constants
- **Punkt rozszerzenia:** Mozna dodac `execute_process_query()` ktory automatycznie dodaje sortowanie po dacie/statusie.

#### `dialect.py` (DialectHelper)
- **Co robi:** Reguły dialektow Oracle vs PostgreSQL, generowanie dokumentacji i przykladow z schema
- **Stan:** KOMPLETNY
- **Kluczowe:** ORACLE_RULES (11 regul), POSTGRESQL_RULES (10 regul), automatyczne generowanie przykladow JOIN/AGG
- **Zaleznosci:** models.connection, models.schema
- **Punkt rozszerzenia:** Mozna dodac `get_process_examples()` generujace przyklady query procesowych.

---

### 2.3 State Layer (`biai/state/`)

#### `__init__.py`
- **Stan:** STUB (pusty)

#### `base.py` (BaseState)
- **Co robi:** Bazowy stan z sidebar toggle/section
- **Stan:** KOMPLETNY (minimalny)
- **Zmienne:** `sidebar_open`, `sidebar_section` ("connection"|"schema"|"settings")
- **Zaleznosci:** reflex

#### `chat.py` (ChatState)
- **Co robi:** Zarzadza czatem - wiadomosci, streaming AI, integracja z pipeline
- **Stan:** KOMPLETNY (najwazniejszy state)
- **Kluczowe zmienne:** `messages: list[dict]`, `input_value`, `is_streaming`, `is_processing`, `_schema_trained`, `confirm_clear`
- **Metody:** `process_message()` (background task - caly flow), `_update_last_message()`, `_strip_latex()`, `cancel_streaming()`
- **Zaleznosci:** state.database, state.query, state.chart, ai.pipeline, components.model_selector
- **Punkt rozszerzenia:** `process_message()` to glowny punkt wejscia. Po `result.success` mozna dodac krok detekcji procesu biznesowego i ustawienia `ProcessVisualizationState`.

#### `query.py` (QueryState)
- **Co robi:** Przechowuje wyniki zapytania SQL, dane tabeli, CSV export
- **Stan:** KOMPLETNY
- **Kluczowe zmienne:** `current_sql`, `columns`, `rows`, `row_count`, `execution_time_ms`, `is_truncated`
- **Computed vars:** `csv_data`, `has_data`, `display_rows` (max 100), `execution_time_display`
- **Zaleznosci:** config.constants
- **Punkt rozszerzenia:** Mozna dodac `process_data: list[dict]` do przechowywania przetworzonych danych procesowych.

#### `schema.py` (SchemaState)
- **Co robi:** Stan schema explorera - lista tabel, kolumn, wyszukiwanie
- **Stan:** KOMPLETNY
- **Kluczowe zmienne:** `tables`, `selected_table`, `selected_columns`, `_tables_full` (transient)
- **Metody:** `refresh_schema()` (background - rekonstruuje konektor z config, nie z `_connector`)
- **Zaleznosci:** state.database, models.connection, db.oracle/postgresql, db.schema_manager

#### `chart.py` (ChartState)
- **Co robi:** Przechowuje konfiguracje wykresu Plotly jako dict
- **Stan:** KOMPLETNY
- **Kluczowe zmienne:** `plotly_fig_data: dict`, `show_plotly`, `chart_title`, `chart_version` (key for re-mount)
- **Metody:** `set_plotly(data, layout, title)`, `clear_chart()`
- **Computed vars:** `plotly_figure` -> `go.Figure`
- **Zaleznosci:** plotly.graph_objects
- **Punkt rozszerzenia:** Mozna dodac osobny `ProcessChartState` z typami wizualizacji procesowych (flow, timeline, Sankey).

#### `database.py` (DBState)
- **Co robi:** Zarzadza polaczeniem DB - formularz, connect/disconnect, auto-refresh schema
- **Stan:** KOMPLETNY (duzy - 236 linii)
- **Kluczowe zmienne:** Pola formularza (db_type, host, port, database, username, password, dsn), status (is_connected, is_connecting, server_version, connection_error), `_connector` (transient)
- **Metody:** `connect()`, `disconnect()`, `test_connection()`, `_get_config()`, `_friendly_error()`
- **Zaleznosci:** config.constants, models.connection, db.oracle/postgresql, db.schema_manager, state.schema/chat/query/chart

#### `presets.py` (PresetsState)
- **Co robi:** CRUD dla zapisanych presetow polaczen (JSON na dysku, hasla szyfrowane)
- **Stan:** KOMPLETNY
- **Kluczowe zmienne:** `presets`, `show_save_dialog`, `show_delete_confirm`
- **Metody:** `load_presets()`, `save_preset()`, `load_preset()`, `confirm_delete()`
- **Zaleznosci:** state.database, utils.connection_storage, utils.crypto

#### `process.py` (ProcessState)
- **Co robi:** Stan wizualizacji procesu React Flow — nodes, edges, metryki, bottleneck, layout toggle, node selection
- **Stan:** KOMPLETNY (96 LOC)
- **Kluczowe zmienne:** `flow_nodes`, `flow_edges`, `process_name`, `show_process`, `layout_direction`, `bottleneck_label`, `total_transitions`, `selected_node_id`
- **Metody:** `set_process_data()`, `clear_process()`, `toggle_layout()`, `on_node_click()`
- **Computed vars:** `has_metrics`, `total_transitions_display`
- **Zaleznosci:** reflex

#### `process_map.py` (ProcessMapState)
- **Co robi:** Stan discovery procesow — lista odkrytych procesow, uruchamianie discovery pipeline, wyswietlanie kart procesow
- **Stan:** KOMPLETNY
- **Kluczowe zmienne:** `discovered_processes`, `is_discovering`, `discovery_error`
- **Metody:** `discover_processes()` (background task), `select_process()`
- **Zaleznosci:** state.database, ai.process_discovery, ai.process_cache, models.discovery

---

### 2.4 Components Layer (`biai/components/`)

#### `__init__.py`
- **Stan:** STUB (pusty)

#### `layout.py` (main_layout)
- **Co robi:** Glowny layout: sidebar + split-screen (chat 40% | dashboard 60%)
- **Stan:** KOMPLETNY
- **Struktura:** `box > hstack > [sidebar | hstack > [chat_panel | dashboard_panel]]`
- **Zaleznosci:** state.base, config.constants, sidebar, chat_panel, dashboard_panel
- **Punkt rozszerzenia:** Mozna dodac trzeci panel (process visualization) lub zamienic dashboard na tabbed layout z zakladkami (Data | Chart | Process).

#### `sidebar.py` (sidebar)
- **Co robi:** Sidebar z 3 zakladkami: Connection, Schema, Settings
- **Stan:** KOMPLETNY
- **Sekcje:** Connection form + model selector | Schema explorer | Settings panel (inline)
- **Zaleznosci:** state.base/database, connection_form, schema_explorer, model_selector, pages.settings

#### `chat_panel.py` (chat_panel)
- **Co robi:** Panel czatu z lista wiadomosci, input, przycisk send/stop, empty state z sugestiami
- **Stan:** KOMPLETNY
- **Kluczowe:** `rx.foreach(ChatState.messages, chat_message)`, form submit, cancel streaming
- **Zaleznosci:** state.chat/query/chart, chat_message

#### `chat_message.py` (chat_message)
- **Co robi:** Pojedynczy bubble wiadomosci z avatar, markdown content, badge'ami SQL/Data/Chart
- **Stan:** KOMPLETNY
- **Kluczowe:** Rozne style dla user/assistant/error, streaming spinner
- **Zaleznosci:** reflex

#### `dashboard_panel.py` (dashboard_panel)
- **Co robi:** Panel dashboard: header z CSV export + chart_card + data_table + sql_viewer
- **Stan:** KOMPLETNY
- **Kluczowe:** CSS display toggle (nie rx.cond) dla unikniecia React hooks warnings
- **Zaleznosci:** state.query/chart, chart_card, data_table, sql_viewer
- **Punkt rozszerzenia:** To glowny punkt do dodania wizualizacji procesow. Mozna dodac nowy komponent `process_flow_card()` miedzy chart_card a data_table, lub jako nowa zakladka.

#### `chart_card.py` (chart_card)
- **Co robi:** Karta z wykresem Plotly
- **Stan:** KOMPLETNY
- **Kluczowe:** `rx.plotly(data=ChartState.plotly_figure, key=ChartState.chart_version)` - key wymusza re-mount
- **Zaleznosci:** state.chart

#### `data_table.py` (data_table)
- **Co robi:** Tabela wynikow z headerem (rows count, execution time, truncated badge)
- **Stan:** KOMPLETNY
- **Kluczowe:** `rx.table.root` + `rx.foreach` na `display_rows` (max 100)
- **Zaleznosci:** state.query

#### `sql_viewer.py` (sql_viewer)
- **Co robi:** Podglad wygenerowanego SQL z syntax highlighting, copy, dialect badge, attempt badge
- **Stan:** KOMPLETNY
- **Kluczowe:** `rx.code_block(language="sql")`, `rx.set_clipboard()`
- **Zaleznosci:** state.query

#### `schema_explorer.py` (schema_explorer)
- **Co robi:** Eksplorator schema - lista tabel, wyszukiwanie, kolumny wybranej tabeli
- **Stan:** KOMPLETNY
- **Kluczowe:** Flat list (nie nested foreach - Reflex limitation), osobna sekcja kolumn
- **Zaleznosci:** state.schema/database

#### `model_selector.py` (ModelState + model_selector)
- **Co robi:** Selektor modelu Ollama z refresh (HTTP call do `/api/tags`)
- **Stan:** KOMPLETNY
- **Kluczowe:** State + Component w jednym pliku, background task dla HTTP call
- **Zaleznosci:** config.constants, httpx

#### `connection_form.py` (connection_form)
- **Co robi:** Formularz polaczenia DB (typ, host, port, database, user, password, DSN)
- **Stan:** KOMPLETNY
- **Kluczowe:** Presets section na gorze, Connect/Disconnect/Reconnect buttons
- **Zaleznosci:** state.database, connection_presets

#### `connection_presets.py` (connection_presets)
- **Co robi:** CRUD UI dla presetow polaczen (lista, save dialog, delete confirm)
- **Stan:** KOMPLETNY
- **Kluczowe:** `rx.dialog.root` (save), `rx.alert_dialog.root` (delete confirm), color-coded ikony PG/Oracle
- **Zaleznosci:** state.presets

#### `process_map_card.py` (process_map_card)
- **Co robi:** UI karty discovery procesow — lista odkrytych procesow z przyciskiem "Discover Processes", wizualizacja wynikow discovery
- **Stan:** KOMPLETNY
- **Kluczowe:** Lista `DiscoveredProcess` z metadata, przycisk uruchamiajacy discovery pipeline
- **Zaleznosci:** state.process_map

#### `react_flow/__init__.py`
- **Co robi:** Package init z eksportami React Flow komponentow
- **Stan:** KOMPLETNY (18 LOC)
- **Zaleznosci:** react_flow.wrapper, react_flow.process_flow

#### `react_flow/wrapper.py` (ReactFlowLib)
- **Co robi:** `ReactFlowLib(rx.NoSSRComponent)` — wrapper @xyflow/react@12.9.0 z 5 custom node types: processStart, processEnd, processTask, processGateway, processCurrent
- **Stan:** KOMPLETNY (176 LOC)
- **Kluczowe klasy:** `ReactFlowLib`, `Background`, `Controls`, `MiniMap`, `ReactFlowProvider`
- **Kluczowe:** Custom JS node types z glow effects, dark theme, bottleneck pulse animation
- **Zaleznosci:** reflex (NoSSRComponent), @xyflow/react@12.9.0 (npm)

#### `react_flow/process_flow.py` (process_flow_card)
- **Co robi:** Komponent React Flow canvas (400px height) + metrics bar + node selection — glowna wizualizacja procesu w dashboard
- **Stan:** KOMPLETNY (120 LOC)
- **Kluczowe:** Header z toggle layout, canvas z Background/Controls/MiniMap, metrics bar (bottleneck + transitions)
- **Zaleznosci:** state.process, react_flow.wrapper

---

### 2.5 Config (`biai/config/`)

#### `settings.py` (AppSettings)
- **Co robi:** Konfiguracja przez pydantic-settings + .env file
- **Stan:** KOMPLETNY
- **Pola:** ollama_host/model, chroma_host/collection, oracle/postgresql DSN, encryption_key, debug, log_level, query timeout/limit
- **Zaleznosci:** pydantic_settings, config.constants

#### `constants.py`
- **Co robi:** Stale aplikacji (AI, DB, UI, SQL Security)
- **Stan:** KOMPLETNY
- **Kluczowe:** MAX_RETRIES=5, DEFAULT_MODEL="qwen2.5-coder:7b-instruct-q4_K_M", QUERY_TIMEOUT=30, ROW_LIMIT=10000, BLOCKED_KEYWORDS (16), BLOCKED_PATTERNS (6)

---

### 2.6 Models (`biai/models/`)

#### `connection.py`
- **Co robi:** DBType enum (ORACLE, POSTGRESQL), ConnectionConfig (Pydantic), DBConnection
- **Stan:** KOMPLETNY
- **Metody:** `get_oracle_dsn()`, `get_postgresql_dsn()`, `display_name`

#### `message.py`
- **Co robi:** MessageRole enum, ChatMessage model
- **Stan:** KOMPLETNY (ale ChatState uzywa dict zamiast ChatMessage - uproszczenie dla Reflex foreach)

#### `schema.py`
- **Co robi:** ColumnInfo, TableInfo (z `get_ddl()`), SchemaSnapshot
- **Stan:** KOMPLETNY
- **Punkt rozszerzenia:** Mozna dodac `ProcessTableInfo` rozszerzajacy `TableInfo` o metadata procesowe (status_column, date_columns, flow_type).

#### `query.py`
- **Co robi:** SQLQuery, QueryResult (z `to_dataframe()`, `to_csv()`), QueryError
- **Stan:** KOMPLETNY
- **Kluczowe:** `to_dataframe()` zawiera Decimal coercion fix

#### `chart.py`
- **Co robi:** ChartType enum (BAR, LINE, PIE, SCATTER, AREA, HEATMAP, TABLE, PROCESS_FLOW, TIMELINE, SANKEY), ChartConfig
- **Stan:** KOMPLETNY
- **Kluczowe:** Dodane typy PROCESS_FLOW, TIMELINE, SANKEY dla wizualizacji procesow

#### `process.py`
- **Co robi:** Modele danych wizualizacji procesow — ProcessNode, ProcessEdge, ProcessFlowConfig z metoda `to_react_flow_data()`
- **Stan:** KOMPLETNY (115 LOC)
- **Kluczowe klasy:** `ProcessNode`, `ProcessEdge`, `ProcessFlowConfig`, `ProcessNodeType` (enum: START, END, TASK, GATEWAY, CURRENT), `ProcessEdgeType`
- **Kluczowe metody:** `ProcessFlowConfig.to_react_flow_data()` — konwertuje na format React Flow (nodes/edges dicts)
- **Zaleznosci:** pydantic

#### `discovery.py`
- **Co robi:** Modele danych discovery procesow — DiscoveredProcess, ColumnCandidate, TransitionPattern, EntityChain
- **Stan:** KOMPLETNY
- **Kluczowe klasy:** `DiscoveredProcess`, `ColumnCandidate`, `TransitionPattern`, `EntityChain`
- **Kluczowe:** Struktura wynikow auto-discovery z ProcessDiscoveryEngine
- **Zaleznosci:** pydantic

---

### 2.7 Utils (`biai/utils/`)

#### `logger.py`
- **Co robi:** Structured logging z structlog (ISO timestamps, console renderer)
- **Stan:** KOMPLETNY

#### `crypto.py`
- **Co robi:** Szyfrowanie hasel presetow (Fernet, klucz w `~/.biai/.key`)
- **Stan:** KOMPLETNY

#### `connection_storage.py` (ConnectionStorage)
- **Co robi:** CRUD JSON storage dla presetow polaczen (`~/.biai/connections.json`)
- **Stan:** KOMPLETNY

---

### 2.8 Pages (`biai/pages/`)

#### `index.py`
- **Co robi:** Glowna strona - wywoluje `main_layout()`
- **Stan:** KOMPLETNY (minimalny)

#### `settings.py` (SettingsState + settings_page)
- **Co robi:** Strona ustawien + state z polami konfiguracyjnymi (Ollama, ChromaDB, Query)
- **Stan:** KOMPLETNY
- **Kluczowe:** Save propaguje do ModelState, Reset przywraca domyslne

---

### 2.9 Root

#### `biai.py`
- **Co robi:** Entry point - tworzy `rx.App()` z dark theme (violet accent), dodaje strony
- **Stan:** KOMPLETNY
- **Strony:** `/` (index), `/settings`
- **Stylesheets:** `/styles/global.css`

---

## 3. Podsumowanie Stanow

| Modul | Liczba Plikow | Kompletny | Czesciowy | Stub |
|-------|---------------|-----------|-----------|------|
| AI Layer | 15 | 14 | 0 | 1 (__init__) |
| DB Layer | 7 | 6 | 0 | 1 (__init__) |
| State Layer | 10 | 9 | 0 | 1 (__init__) |
| Components | 14 | 13 | 0 | 1 (__init__) |
| Config | 2 | 2 | 0 | 0 |
| Models | 7 | 7 | 0 | 0 |
| Utils | 3 | 3 | 0 | 0 |
| Pages | 2 | 2 | 0 | 0 |
| Root | 1 | 1 | 0 | 0 |
| Tests | 7 | 7 | 0 | 0 |
| **RAZEM** | **~68** | **~64** | **0** | **4** |

**Wniosek:** Cala funkcjonalnosc jest KOMPLETNA. 7 plikow testow w `tests/` i `biai/tests/` pokrywa ~40-50% kodu (chart_advisor, schema_manager, query_executor, connectors — jeszcze bez testow).

---

## 4. Graf Zaleznosci (uproszczony)

```
pages/index.py
  -> components/layout.py
      -> components/sidebar.py
      |     -> components/connection_form.py -> state/database.py
      |     |     -> components/connection_presets.py -> state/presets.py
      |     -> components/schema_explorer.py -> state/schema.py
      |     -> components/model_selector.py (ModelState)
      |     -> pages/settings.py (SettingsState)
      -> components/chat_panel.py
      |     -> components/chat_message.py
      |     -> state/chat.py
      |          -> state/database.py -> db/oracle.py, db/postgresql.py
      |          -> state/query.py
      |          -> state/chart.py
      |          -> state/process.py
      |          -> ai/pipeline.py
      |               -> ai/vanna_client.py (Vanna + ChromaDB + Ollama)
      |               -> ai/sql_validator.py (sqlglot)
      |               -> ai/self_correction.py
      |               -> ai/chart_advisor.py
      |               -> ai/training.py
      |               -> ai/prompt_templates.py
      |               -> ai/process_detector.py -> models/process.py
      |               -> ai/process_graph_builder.py -> models/process.py
      |               -> ai/process_discovery.py -> models/discovery.py
      |               -> ai/process_cache.py
      |               -> ai/process_training.py
      |               -> ai/process_training_dynamic.py -> models/discovery.py
      |               -> ai/dynamic_styler.py
      |               -> ai/process_layout.py
      |               -> db/schema_manager.py -> db/base.py
      |               -> db/query_executor.py -> db/base.py
      |               -> db/dialect.py
      -> components/dashboard_panel.py
            -> components/chart_card.py -> state/chart.py
            -> components/data_table.py -> state/query.py
            -> components/sql_viewer.py -> state/query.py
            -> components/process_map_card.py -> state/process_map.py
            -> components/react_flow/process_flow.py -> state/process.py
                  -> components/react_flow/wrapper.py (@xyflow/react)
```

---

## 5. Punkty Rozszerzenia dla Wizualizacji Procesow Biznesowych

### 5.1 Warstwa AI (najwyzszy priorytet)

| Plik | Punkt rozszerzenia | Opis |
|------|-------------------|------|
| `ai/pipeline.py` | `PipelineResult` | Dodac pole `process_data`, `process_config` |
| `ai/pipeline.py` | `process()` | Dodac krok detekcji procesu po `chart_advisor.recommend()` |
| `ai/chart_advisor.py` | `ChartType` + `_heuristic_recommend()` | Nowe typy: PROCESS_FLOW, GANTT, SANKEY, TIMELINE |
| `ai/prompt_templates.py` | Nowe prompty | PROCESS_DETECTION_PROMPT, PROCESS_DESCRIPTION_PROMPT |
| `ai/training.py` | `train_process_knowledge()` | Nauczenie Vanna o relacjach procesowych |

### 5.2 Warstwa Models

| Plik | Punkt rozszerzenia | Opis |
|------|-------------------|------|
| `models/chart.py` | `ChartType` enum | Dodac PROCESS_FLOW, GANTT, SANKEY, TIMELINE |
| `models/chart.py` | Nowy model | `ProcessVisualizationConfig` z polami flow_type, nodes, edges |
| `models/schema.py` | `SchemaSnapshot` | Dodac metadata procesowe (np. detected_process_tables) |

### 5.3 Warstwa State

| Plik | Punkt rozszerzenia | Opis |
|------|-------------------|------|
| `state/chat.py` | `process_message()` | Dodac krok process detection + set ProcessState |
| `state/chart.py` | Nowy state | `ProcessVisualizationState` z danymi flow/timeline |
| `state/query.py` | `set_query_result()` | Opcjonalnie: wykrywanie danych procesowych w wynikach |

### 5.4 Warstwa Components (UI)

| Plik | Punkt rozszerzenia | Opis |
|------|-------------------|------|
| `components/dashboard_panel.py` | Nowy komponent | `process_flow_card()` miedzy chart_card a data_table |
| `components/layout.py` | Layout | Dodac tab/panel dla wizualizacji procesow |
| `components/chat_message.py` | Badge | Dodac badge "Process" obok "Chart"/"Data" |

### 5.5 Najlepsza strategia integracji

**Rekomendacja: Minimalna ingerencja w istniejacy kod.**

1. **Nowy modul `biai/ai/process_detector.py`** - detektuje procesy w danych (kolumny statusowe, daty etapow, FK chains)
2. **Nowy model `biai/models/process.py`** - ProcessVisualizationConfig, ProcessNode, ProcessEdge
3. **Nowy state `biai/state/process.py`** - ProcessVisualizationState
4. **Nowy component `biai/components/process_flow.py`** - renderuje wizualizacje procesu
5. **Modyfikacja `chat.py`** - po `result.success`, wywolaj process detection
6. **Modyfikacja `dashboard_panel.py`** - dodaj `process_flow_card()`
7. **Modyfikacja `chart.py` (model)** - dodaj nowe ChartType

Istniejacy kod jest dobrze zmodularyzowany i mozna go rozszerzac bez laczenia logiki.

---

## 6. Metryki Kodu

| Kategoria | Pliki | LOC (szacunkowo) |
|-----------|-------|-------------------|
| AI Layer | 14 (+1 stub) | ~1500 |
| DB Layer | 6 (+1 stub) | ~500 |
| State Layer | 9 (+1 stub) | ~1000 |
| Components | 13 (+1 stub) | ~950 |
| Config | 2 | ~100 |
| Models | 7 | ~400 |
| Utils | 3 | ~100 |
| Pages | 2 | ~250 |
| Root | 1 | ~30 |
| Tests | 7 | ~700 |
| **RAZEM** | **~64 (+4 stub)** | **~5500+** |

---

## 7. Potencjalne Problemy / Uwagi

1. **ChatState `messages` to `list[dict]`** - nie `list[ChatMessage]` - uproszczenie dla Reflex foreach, ale mniej type-safe
2. **SchemaState `_tables_full`** - transient (`_` prefix) - nie przezywa background task serialization; `refresh_schema()` rekonstruuje konektor z config zamiast uzywac `_connector`
3. **`_build_plotly_figure()` w chat.py** - ta funkcja powinna byc w osobnym module (np. `utils/plotly_builder.py`), jest duza (~85 linii)
4. **Testy** - 7 plikow testow w `tests/` i `biai/tests/`: `conftest.py`, `test_sql_validator.py`, `test_self_correction.py`, `test_pipeline.py`, `test_discovery.py`, `test_process.py` + inne. Pokrycie ~40-50% kodu (chart_advisor, schema_manager, query_executor, connectors — jeszcze bez testow)
5. **Brak CI/CD** - brak `.github/workflows/` lub podobnego
6. **`model_selector.py` laczy State + Component** - ModelState powinien byc w `state/` dla spojnosci

---

## 8. Technologie i Biblioteki

| Kategoria | Biblioteka | Wersja/Rola |
|-----------|-----------|-------------|
| Frontend | Reflex | 0.8.x (Python web framework) |
| AI/NLP | Vanna.ai | Text-to-SQL via RAG |
| LLM | Ollama | Lokalne LLM (default: qwen2.5-coder:7b) |
| VectorDB | ChromaDB | Embedding store dla Vanna |
| SQL Parse | sqlglot | AST validation + transpilation |
| Charts | Plotly | Interaktywne wykresy |
| PostgreSQL | asyncpg | Natywny async driver |
| Oracle | oracledb | Thin mode driver |
| Config | pydantic-settings | .env file config |
| Logging | structlog | Structured logging |
| Crypto | cryptography | Fernet encryption (hasla presetow) |
| HTTP | httpx | Async HTTP client (Ollama API) |

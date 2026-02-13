# BIAI - Analiza POC vs Implementacja: Lista Niezaimplementowanych Wymagan

**Data analizy:** 2026-02-13
**Analizowane dokumenty:** `docs/poc.md`, `docs/architecture.md`
**Analizowany kod:** `biai/**/*.py` (49 plikow)

---

## Podsumowanie

| Status | Liczba wymagan |
|--------|---------------|
| DONE | 32 |
| PARTIAL | 7 |
| NOT_IMPLEMENTED | 11 |
| **TOTAL** | **50** |

---

## 1. Stack Technologiczny

### 1.1 Jezyk i framework
| # | Wymaganie POC | Status | Uwagi |
|---|--------------|--------|-------|
| 1 | Python 3.10+ | DONE | Uzywa type hints `str \| None` (3.10+) |
| 2 | Streamlit (POC) -> Reflex (architecture.md) | DONE | Zmieniono na Reflex 0.8.x - swiadoma decyzja architektoniczna |
| 3 | Layout wide / dwukolumnowy (Chat + Dashboard) | DONE | `layout.py`: 40% chat + 60% dashboard split-screen |

### 1.2 Wizualizacja
| # | Wymaganie POC | Status | Trudnosc | Priorytet | Uwagi |
|---|--------------|--------|----------|-----------|-------|
| 4 | Plotly (standardowe wykresy biznesowe) | DONE | - | - | `chart_card.py` + `rx.plotly()` |
| 5 | **ECharts (animowane, nowoczesne wykresy)** | **NOT_IMPLEMENTED** | 3 | 4 | POC wymaga "dark mode, animacje, efekt glow". Aktualnie TYLKO Plotly. `architecture.md` wymienia ECharts ale brak implementacji |
| 6 | **Mermaid.js (diagramy ERD i sekwencji)** | **NOT_IMPLEMENTED** | 4 | 5 | KLUCZOWY PRIORYTET. POC wymaga diagramow procesowych/przeplywow. Brak jakiejkolwiek implementacji |
| 7 | **Graphviz (diagramy procesowe)** | **NOT_IMPLEMENTED** | 3 | 4 | Alternatywa do Mermaid. Brak implementacji |

### 1.3 Baza danych
| # | Wymaganie POC | Status | Uwagi |
|---|--------------|--------|-------|
| 8 | python-oracledb (thin mode) | DONE | `oracle.py` - async pool, thin mode |
| 9 | PostgreSQL (rozszerzenie) | DONE | `postgresql.py` - asyncpg pool |
| 10 | Abstrakcyjna klasa DatabaseConnector | DONE | `base.py` - ABC z connect(), get_schema_summary(), execute_query() |
| 11 | MongoDB (przyszlosc) | NOT_IMPLEMENTED | 1 | 1 | POC mowi "przygotowana na rozszerzenie" - architektura to umozliwia |

### 1.4 AI/LLM Backend
| # | Wymaganie POC | Status | Uwagi |
|---|--------------|--------|-------|
| 12 | Ollama (komunikacja z lokalnym modelem) | DONE | `vanna_client.py` + httpx streaming |
| 13 | Vanna.ai (RAG text-to-SQL) | DONE | `vanna_client.py` - ChromaDB + Ollama |
| 14 | ChromaDB (vector store) | DONE | Zintegrowany z Vanna |
| 15 | sqlglot (parser/walidacja SQL) | DONE | `sql_validator.py` - AST parsing + transpilacja |
| 16 | Prompt Engineering (bez LangChain) | DONE | `prompt_templates.py` - custom prompts |
| 17 | pandas (przetwarzanie danych) | DONE | DataFrame w pipeline, QueryResult.to_dataframe() |

---

## 2. Architektura i Wzorce Projektowe

### 2.1 Modularnosc (Konektory)
| # | Wymaganie POC | Status | Uwagi |
|---|--------------|--------|-------|
| 18 | Abstrakcyjny DatabaseConnector | DONE | `db/base.py` |
| 19 | OracleConnector | DONE | `db/oracle.py` - pool, async, thin mode |
| 20 | PostgreSQLConnector | DONE | `db/postgresql.py` - asyncpg pool |
| 21 | Metody: connect(), get_schema_summary(), execute_query() | DONE | Plus: disconnect(), test_connection(), get_server_version() |

### 2.2 Agent Workflow (Przeplyw Danych)
| # | Wymaganie POC | Status | Trudnosc | Priorytet | Uwagi |
|---|--------------|--------|----------|-----------|-------|
| 22 | User Input -> Chat | DONE | - | - | `chat_panel.py` + `ChatState` |
| 23 | Schema Retrieval -> Context | DONE | - | - | `SchemaManager` + `SchemaTrainer` (RAG) |
| 24 | Reasoning: LLM decyduje "SQL czy diagram?" | **NOT_IMPLEMENTED** | 4 | 5 | KLUCZOWY BRAK. Pipeline ZAWSZE generuje SQL. Nie ma logiki routing: "dane liczbowe vs diagram procesu" |
| 25 | Action (SQL path): LLM -> SQL -> execute -> DataFrame | DONE | - | - | `pipeline.py` process() |
| 26 | **Action (diagram path): LLM -> Mermaid/Graphviz** | **NOT_IMPLEMENTED** | 5 | 5 | KLUCZOWY PRIORYTET. Brak sciezki generowania diagramow |
| 27 | Visualization: LLM decyduje typ wizualizacji | DONE | - | - | `ChartAdvisor` (heuristic + LLM) |
| 28 | Render: UI wyswietla wynik | DONE | - | - | `dashboard_panel.py` (chart + table + SQL) |

---

## 3. Wymagania Funkcjonalne (MVP)

### 3.1 Interfejs Uzytkownika
| # | Wymaganie POC | Status | Uwagi |
|---|--------------|--------|-------|
| 29 | Sidebar: Konfiguracja polaczenia (Host, Port, Service, User, Pass) | DONE | `connection_form.py` - pelny formularz |
| 30 | Sidebar: Przycisk "Polacz i Pobierz Schemat" | DONE | `DBState.connect()` + auto schema refresh |
| 31 | Sidebar: Wybor modelu Ollama z listy | DONE | `model_selector.py` + refresh z API |
| 32 | Chat: Historia rozmowy, pole input | DONE | `chat_panel.py` - foreach messages |
| 33 | Chat: Stylizacja dymkow (User vs AI) | DONE | `chat_message.py` - rozne kolory, avatar |
| 34 | Dashboard: Karta z wykresem | DONE | `chart_card.py` - Plotly |
| 35 | **Dashboard: Opcja powiekszenia wykresu** | **NOT_IMPLEMENTED** | 2 | 3 | Brak fullscreen/zoom mode dla wykresu |
| 36 | **Dashboard: Diagramy Mermaid renderowane jako HTML** | **NOT_IMPLEMENTED** | 4 | 5 | Brak renderowania Mermaid |
| 37 | Dashboard: Tabele danych | DONE | `data_table.py` - rx.table z scrollem |

### 3.2 Logika Biznesowa
| # | Wymaganie POC | Status | Uwagi |
|---|--------------|--------|-------|
| 38 | Text-to-SQL (poprawny Oracle dialect) | DONE | Vanna + dialect rules + sqlglot transpilation |
| 39 | Ochrona: tylko SELECT (read-only) | DONE | 4 warstwy: blocked keywords, regex, AST, single statement |
| 40 | Samonaprawa: blad SQL -> ponowna proba z LLM | DONE | `self_correction.py` - max 5 prob z error feedback |

### 3.3 Pozostale wymagania
| # | Wymaganie POC | Status | Trudnosc | Priorytet | Uwagi |
|---|--------------|--------|----------|-----------|-------|
| 41 | Czysty kod, type hints, PEP8 | DONE | - | - | Konsekwentne type hints, modularnosc |
| 42 | Try-except przy polaczeniu i query | DONE | - | - | Obsluga bledow w connectorach, pipeline, executor |
| 43 | **Tryb Demo z zahardkodowanym DataFrame** | **NOT_IMPLEMENTED** | 3 | 3 | POC: "Jesli nie uda sie polaczyc z baza, dodaj Tryb Demo". Brak implementacji |
| 44 | **ECharts: Dark Mode, animacje, efekt "glow"** | **NOT_IMPLEMENTED** | 3 | 4 | POC: "wykresy ECharts wyglądały nowocześnie". Brak ECharts |
| 45 | Docker setup (Oracle XE w Docker) | DONE | - | - | `docker-compose.dev.yml` |
| 46 | Docker deploy | PARTIAL | - | - | `Dockerfile` + `docker-compose.yml` istnieja |

---

## 4. Architecture.md - dodatkowe wymagania

| # | Wymaganie | Status | Trudnosc | Priorytet | Uwagi |
|---|----------|--------|----------|-----------|-------|
| 47 | ECharts + Plotly (oba) | PARTIAL | 3 | 4 | Tylko Plotly zaimplementowany |
| 48 | Security 4 layers | DONE | - | - | sqlglot AST, regex, single stmt, blocked keywords |
| 49 | Stream description | DONE | - | - | `pipeline.generate_description()` - async streaming |
| 50 | pydantic-settings | PARTIAL | - | - | Uzywa pydantic BaseModel ale nie pydantic-settings |

---

## 5. Zestawienie NOT_IMPLEMENTED (priorytetowane)

| Priorytet | # | Wymaganie | Trudnosc (1-5) | Opis |
|-----------|---|----------|---------------|------|
| **5 (krytyczny)** | 24 | Agent Routing: SQL vs Diagram | 4 | Pipeline musi decydowac czy pytanie wymaga SQL czy diagramu procesu |
| **5 (krytyczny)** | 26 | Sciezka generowania diagramow (Mermaid/Graphviz) | 5 | LLM generuje kod Mermaid na podstawie danych w bazie |
| **5 (krytyczny)** | 6 | Renderowanie Mermaid.js w UI | 4 | Komponent Reflex do renderowania Mermaid jako HTML/SVG |
| **5 (krytyczny)** | 36 | Dashboard: Mermaid diagrams | 4 | Integracja renderera Mermaid w dashboard panel |
| **4 (wysoki)** | 5 | ECharts (animowane wykresy) | 3 | Alternatywa/uzupelnienie Plotly z dark mode i animacjami |
| **4 (wysoki)** | 44 | ECharts: dark mode, glow effects | 3 | Nowoczesny styl wykresow |
| **4 (wysoki)** | 7 | Graphviz (jako alternatywa Mermaid) | 3 | Opcjonalny - Mermaid pokrywa wiekszosc przypadkow |
| **3 (sredni)** | 43 | Tryb Demo z mock data | 3 | Pokaz mozliwosci UI bez polaczenia z DB |
| **3 (sredni)** | 35 | Fullscreen/zoom wykresu | 2 | UX enhancement |
| **1 (niski)** | 11 | MongoDB connector | 1 | POC: "przygotowana na rozszerzenie" |

---

## 6. Zestawienie PARTIAL

| # | Wymaganie | Co jest | Czego brakuje |
|---|----------|---------|---------------|
| 46 | Docker deploy | Dockerfile + compose istneja | Brak testow, brak CI/CD |
| 47 | ECharts + Plotly | Plotly dziala | ECharts niezaimplementowany |
| 50 | pydantic-settings | pydantic BaseModel | Brak .env loading, brak Settings class |

---

## 7. Co jest zaimplementowane PONAD wymagania POC

Aplikacja zawiera funkcje, ktore NIE byly w POC ale sa wartosciowe:

| Funkcja | Plik | Opis |
|---------|------|------|
| Connection Presets (CRUD) | `connection_presets.py`, `presets.py` | Zapisywanie/ladowanie/edycja/usuwanie polaczen |
| Szyfrowanie hasel | `crypto.py`, `connection_storage.py` | Encrypted storage dla presetow |
| Schema Explorer | `schema_explorer.py`, `schema.py` | Przegladarka tabel z wyszukiwaniem |
| CSV Export | `dashboard_panel.py`, `query.py` | Download CSV z wynikow |
| SQL Viewer z Copy | `sql_viewer.py` | Podglad SQL + kopiowanie do schowka |
| Settings Page | `settings.py` | Konfiguracja Ollama, ChromaDB, query params |
| Self-correction (5 prob) | `self_correction.py` | Wiecej niz POC wymagal (POC: "ponowna proba") |
| Dialect auto-transpilation | `sql_validator.py` | LIMIT -> FETCH FIRST automatycznie |
| Streaming z cancellation | `chat.py` | Cancel streaming odpowiedzi AI |
| LaTeX stripping | `chat.py` | Czyszczenie formatowania LLM output |
| Oracle bind var sanitization | `sql_validator.py` | Fix :PARAM -> 'PARAM' |

---

## 8. Architektura gap (kluczowe braki strukturalne)

### 8.1 Brak Agent Router
Aktualny pipeline (`pipeline.py:process()`) ZAWSZE idzie sciezka SQL:
```
question -> generate_sql -> validate -> execute -> chart -> description
```

POC wymaga:
```
question -> ROUTING DECISION:
  |
  |- "dane liczbowe" -> SQL path (istniejacy)
  |
  |- "diagram procesu" -> Mermaid/Graphviz path (BRAK!)
  |
  |- "struktura bazy" -> ERD diagram path (BRAK!)
```

### 8.2 Brak warstwy wizualizacji procesow
Caly stos wizualizacji procesow jest niezaimplementowany:
- Brak Mermaid.js integration w Reflex
- Brak Graphviz/DOT rendering
- Brak modeli danych dla diagramow (DiagramConfig, ProcessFlow, etc.)
- Brak prompt templates dla generowania kodu Mermaid
- Brak komponentow UI do wyswietlania diagramow

### 8.3 Brak ECharts
POC i architecture.md wymieniaja ECharts jako kluczowy element:
- "animowane, nowoczesne wykresy"
- "Dark Mode, animacje, efekt glow"
- Aktualnie Plotly pokrywa funkcjonalnosc ale bez efektow wizualnych z POC

---

## 9. Rekomendowana kolejnosc implementacji

### Faza 1: Agent Routing + Mermaid (KRYTYCZNE)
1. **Agent Router** w `pipeline.py` - klasyfikacja pytania (SQL vs diagram)
2. **Mermaid prompt templates** - `prompt_templates.py` rozszerzenie
3. **Mermaid renderer component** - nowy komponent Reflex
4. **Dashboard integration** - Mermaid obok Plotly w dashboard_panel

### Faza 2: ECharts (WYSOKI PRIORYTET)
5. **ECharts component** w Reflex (via `rx.html` lub custom component)
6. **ECharts themes** - dark mode, glow effects
7. **Chart type routing** - Plotly vs ECharts decyzja

### Faza 3: Demo Mode + UX (SREDNI PRIORYTET)
8. **Demo mode** - mock data + sample questions
9. **Chart fullscreen/zoom** - modal/overlay
10. **pydantic-settings** - .env file support

---

## 10. Aktualizacja statusu luk (2026-02-13)

### 10.1 FIXED — Luki naprawione od czasu analizy

| # z raportu | Wymaganie | Status | Co zrobiono |
|-------------|----------|--------|-------------|
| 20 | PostgreSQL Connector | DONE | `postgresql.py` — asyncpg pool, PK/FK detection, schema guard |
| 15 | sqlglot (parser/walidacja SQL) | DONE | 3-warstwowa walidacja + **transpilacja dialektow** (LIMIT -> FETCH FIRST) |
| 40 | Samonaprawa SQL | DONE | `self_correction.py` — max 5 prob, fix empty SQL po refusal |
| 38 | Poprawny dialect SQL | DONE | `vanna_client.py` + `dialect.py` — dialect przekazywany do Vanna, system prompt "You are a {dialect} expert" |
| 23 | Schema Retrieval -> Context | DONE | `training.py` — schema training z DDL + dialect-specific examples + documentation |
| 42 | Try-except obsluga bledow | DONE | Kompleksowa obsluga w connectors, pipeline, executor, self-correction |
| - | Connection Presets | DONE (NOWE) | `connection_presets.py`, `presets.py`, `crypto.py`, `connection_storage.py` — save/load/delete z szyfrowanymi haslami |
| - | CSV Export | DONE (NOWE) | `query.py` csv_data + `dashboard_panel.py` rx.download() |
| 49 | Stream description | DONE | `pipeline.generate_description()` — async streaming z cancellation |
| 50 | pydantic-settings | DONE | `settings.py` — `AppSettings(BaseSettings)` z .env loading |
| 24 | Agent Routing: SQL vs Diagram | DONE (inaczej niz plan) | **Post-hoc ProcessDetector** zamiast pre-routing — pipeline ZAWSZE generuje SQL, procesy wykrywane w wynikach |
| 26 | Sciezka generowania diagramow | DONE (React Flow) | React Flow (@xyflow/react) zamiast Mermaid/Graphviz — interaktywne diagramy z glow effects |
| 36 | Dashboard: Diagramy procesowe | DONE | `process_flow_card()` w dashboard z React Flow canvas, metrics bar, node selection |
| - | Oracle bind variables | DONE (NOWE) | `sql_validator.py` — `:PARAM_NAME` -> `'PARAM_NAME'` |

### 10.2 STILL MISSING — Luki nadal niezaimplementowane

| # z raportu | Wymaganie | Priorytet | Uwagi |
|-------------|----------|-----------|-------|
| 5 | **ECharts** (animowane wykresy z dark mode, glow) | 4 (wysoki) | Plotly pokrywa funkcjonalnosc ale bez efektow wizualnych z POC. React Flow czesciowo spelnia wymaganie glow/dark mode dla procesow. |
| 43 | **Tryb Demo** z zahardkodowanym DataFrame | 3 (sredni) | Brak mozliwosci pokazu UI bez polaczenia z DB |
| 11 | **MongoDB** connector | 1 (niski) | Architektura to umozliwia (ABC DatabaseConnector) ale brak implementacji |
| - | **CI/CD** pipeline | 2 (sredni) | Brak `.github/workflows/` — testy reczne via pytest |
| 35 | **Fullscreen/zoom** wykresu | 2 (sredni) | Plotly ma wbudowany zoom ale brak modal/overlay fullscreen |
| 7 | **Graphviz** (jako alternatywa) | 1 (niski) | React Flow pokrywa wizualizacje procesow, Graphviz niepotrzebny |
| 6 | **Mermaid.js** (diagramy ERD) | 2 (sredni) | React Flow pokrywa procesy; ERD diagrams nadal brak |

### 10.3 Podsumowanie postepow

| Status | Przed | Po aktualizacji |
|--------|-------|-----------------|
| DONE | 32 | 46 |
| PARTIAL | 7 | 2 |
| NOT_IMPLEMENTED | 11 | 7 |
| **TOTAL** | **50** | **55** (+ 5 nowych wymagan) |

**Pokrycie wymagan:** 32/50 (64%) -> 46/55 (84%)

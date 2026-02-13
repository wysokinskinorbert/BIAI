# Plan: Dynamiczne odkrywanie procesow w BIAI

## Context

Aplikacja BIAI ma wizualizacje process flow, ale jest silnie hardcoded - 4 typy procesow, 40+ statusow z recznie przypisanymi kolorami/ikonami, sztywne sekwencje stanow. Uzytkownik chce systemu, ktory **automatycznie odkrywa procesy** z dowolnej bazy danych na podstawie schematu (FK, kolumny statusowe, tabele tranzycji) i danych, a nastepnie prezentuje je w interaktywnej wizualizacji z drill-down.

---

## Faza 1: DynamicStyler - zastapienie hardcoded kolorow/ikon (Quick Win)

**Cel:** Usuniecie `STATUS_COLORS` (40+ wpisow) i `STATUS_ICONS` (40+ wpisow) z `models/process.py`.

### 1.1 Nowy plik: `biai/ai/dynamic_styler.py` (~100 linii)

```python
class DynamicStyler:
    PALETTE = ["#6366f1", "#3b82f6", "#0ea5e9", "#22c55e", "#eab308", "#f97316", "#ef4444", ...]
    SEMANTIC_COLORS = {"success": ["delivered","completed","approved","resolved","won","done"], ...}
    SEMANTIC_ICONS = {"new": "plus-circle", "processing": "loader", "shipped": "truck", ...}

    @classmethod
    def get_color(cls, status_id: str, ai_suggestion: str | None = None) -> str
    @classmethod
    def get_icon(cls, status_id: str, ai_suggestion: str | None = None) -> str
```

- Priorytet: AI suggestion > semantic match (keyword in status_id) > hash-based (deterministyczny)
- Paleta 12 kolorow WCAG AA na dark theme

### 1.2 Modyfikacja: `biai/models/process.py`

- **Usunac:** `STATUS_COLORS` dict (linie 18-34), `STATUS_ICONS` dict (linie 37-52)
- **Zmienic:** `to_react_flow_data()` linie 116-117:
  ```python
  # PRZED:
  color = STATUS_COLORS.get(node.id, STATUS_COLORS["default"])
  icon = STATUS_ICONS.get(node.id, STATUS_ICONS["default"])
  # PO:
  from biai.ai.dynamic_styler import DynamicStyler
  color = DynamicStyler.get_color(node.id, node.metadata.get("ai_color"))
  icon = DynamicStyler.get_icon(node.id, node.metadata.get("ai_icon"))
  ```

### 1.3 Testy w `tests/test_process.py`

- Zamienic `test_status_colors_coverage` i `test_status_icons_coverage` na testy DynamicStyler
- Dodac testy: semantic match, hash determinism, AI suggestion priority

---

## Faza 2: Modele danych odkrywania

### 2.1 Nowy plik: `biai/models/discovery.py` (~80 linii)

```python
class ColumnCandidate(BaseModel):
    table_name: str; column_name: str; role: str  # "status"|"timestamp"|"duration"
    distinct_values: list[str] = []; cardinality: int = 0; confidence: float = 0.0

class TransitionPattern(BaseModel):
    table_name: str; from_column: str; to_column: str
    count_column: str | None; timestamp_column: str | None
    transitions: list[tuple[str, str, int]] = []

class EntityChain(BaseModel):
    tables: list[str]; join_keys: list[tuple[str, str]]; entity_name: str

class DiscoveredProcess(BaseModel):
    id: str; name: str; description: str; tables: list[str]
    status_column: ColumnCandidate | None; transition_pattern: TransitionPattern | None
    entity_chain: EntityChain | None; stages: list[str]
    stage_counts: dict[str, int] = {}; branches: dict[str, list[str]] = {}
    confidence: float = 0.0
    ai_labels: dict[str, str] = {}; ai_colors: dict[str, str] = {}; ai_icons: dict[str, str] = {}
```

---

## Faza 3: ProcessDiscoveryEngine - serce systemu

### 3.1 Nowy plik: `biai/ai/process_discovery.py` (~300 linii)

```python
class ProcessDiscoveryEngine:
    def __init__(self, connector: DatabaseConnector, schema: SchemaSnapshot): ...
    async def discover(self) -> list[DiscoveredProcess]: ...
```

**Metody odkrywania (heurystyczne, bez AI):**

1. **`_find_status_columns()`** - Szukanie kolumn statusowych:
   - Iteracja po SchemaSnapshot.tables[].columns[]
   - Filtr: VARCHAR/TEXT + nazwa pasuje do wzorcow (`status`, `state`, `stage`, `step`, `phase`, `*_status`)
   - Score na podstawie nazwy kolumny (confidence weighting)

2. **`_find_transition_tables()`** - Szukanie par from/to:
   - Pary kolumn: `from_*/to_*`, `old_*/new_*`, `prev_*/next_*`
   - Tabele z sufiksem: `_history`, `_log`, `_audit`, `_transitions`

3. **`_find_fk_chains()`** - Analiza relacji FK:
   - Graf zaleznosci z SchemaSnapshot FK info
   - Lancuchy: A -> B -> C (encja processowa)

4. **`_enrich_with_data()`** - Zapytania diagnostyczne do DB:
   ```sql
   SELECT {status_col}, COUNT(*) FROM {table} GROUP BY {status_col} ORDER BY cnt DESC LIMIT 50
   SELECT {from_col}, {to_col}, COUNT(*) FROM {table} GROUP BY {from_col}, {to_col}
   ```
   - Walidacja: niska kardynalnosc (< 30 unikalnych wartosci)
   - Timeout: 10s per zapytanie

5. **`_ai_interpret()`** - Ollama interpretacja:
   - Prompt z pelnym schema + odkrytymi kandydatami
   - AI nadaje nazwy, opisy, kolory, ikony, sekwencje stanow
   - JSON response parsing z walidacja
   - Fallback na heurystyki jesli AI zawiedzie

### 3.2 Nowy plik: `biai/ai/process_cache.py` (~60 linii)

```python
class ProcessDiscoveryCache:
    def __init__(self, ttl: int = 600): ...
    def get(self, config: ConnectionConfig) -> list[DiscoveredProcess] | None: ...
    def store(self, config: ConnectionConfig, processes: list[DiscoveredProcess]): ...
    def invalidate(self, config: ConnectionConfig): ...
```

- Cache per connection key (db_type:host:port:database)
- TTL 10 minut (konfigurowalne)

### 3.3 Nowe stale w `biai/config/constants.py`

```python
USE_DYNAMIC_DISCOVERY: bool = True
DISCOVERY_MAX_TABLES: int = 50
DISCOVERY_MAX_CARDINALITY: int = 30
DISCOVERY_QUERY_TIMEOUT: int = 10
```

---

## Faza 4: Refaktor ProcessGraphBuilder - usuwanie KNOWN_*

### 4.1 Modyfikacja: `biai/ai/process_graph_builder.py`

- **Usunac:** `KNOWN_SEQUENCES` (linie 21-40), `KNOWN_BRANCHES` (linie 43-47)
- **Rozszerzyc `build()`** o parametr `discovered: DiscoveredProcess | None`:
  ```python
  def build(self, df, process_type, question, discovered=None) -> ProcessFlowConfig | None:
      if self._has_transition_columns(df):        # Strategy 1 (zachowane)
          return self._build_from_transitions(df, process_type, question, discovered)
      if self._has_aggregate_columns(df):          # Strategy 2 (ulepszone)
          return self._build_from_aggregates(df, process_type, question, discovered)
      if discovered and discovered.stages:         # Strategy 3 NOWA
          return self._build_from_discovery(df, question, discovered)
      return None  # zamiast _build_from_known_sequence
  ```
- **Nowa `_build_from_discovery()`** - buduje graf z DiscoveredProcess.stages + branches
- **Ulepszona `_order_states()`** - uzywa `discovered.stages` zamiast KNOWN_SEQUENCES
- **Ulepszona `_build_from_aggregates()`** - uzywa `discovered.branches` zamiast KNOWN_BRANCHES

### 4.2 Modyfikacja: `biai/ai/process_detector.py`

- **Zachowac:** `detect_process_type()` (linie 79-90) z deprecated warning
- **Dodac:** `detect_process_type_dynamic()`:
  ```python
  def detect_process_type_dynamic(self, df, sql, discovered_processes):
      # Dopasowanie tabeli z SQL lub kolumn statusowych do DiscoveredProcess
      return (process_name, discovered_process) | ("generic", None)
  ```

---

## Faza 5: Integracja z Pipeline

### 5.1 Modyfikacja: `biai/ai/pipeline.py`

**W `train_schema()` (linie 106-122):**
```python
# Po istniejacym train_full:
if USE_DYNAMIC_DISCOVERY:
    engine = ProcessDiscoveryEngine(self._connector, snapshot)
    discovered = await engine.discover()
    if discovered:
        trainer = DynamicProcessTrainer()
        docs.extend(trainer.generate_documentation(discovered, snapshot))
        examples.extend(trainer.generate_examples(discovered, is_oracle))
        self._discovered_processes = discovered
# Fallback: zachowac stary if has_process_tables() dla kompatybilnosci
```

**W `process()` (linie 162-179):**
```python
# Uzyj _discovered_processes jesli dostepne:
discovered_procs = getattr(self, '_discovered_processes', [])
if discovered_procs:
    process_type, discovered = detector.detect_process_type_dynamic(df, sql, discovered_procs)
else:
    process_type = detector.detect_process_type(df, sql)
    discovered = None
result.process_config = builder.build(df, process_type, question, discovered=discovered)
```

### 5.2 Nowy plik: `biai/ai/process_training_dynamic.py` (~120 linii)

```python
class DynamicProcessTrainer:
    def generate_documentation(self, processes, schema) -> list[str]: ...
    def generate_examples(self, processes, is_oracle) -> list[tuple[str, str]]: ...
```

- Generuje dokumentacje z odkrytych procesow (nazwy tabel, stany, branche)
- Generuje przyklady SQL z rzeczywistych nazw kolumn i tabel

### 5.3 Nowe prompty w `biai/ai/prompt_templates.py`

```python
PROCESS_DISCOVERY_PROMPT = """Analyze this database schema and identify business processes...
Respond in JSON: [{name, description, stages, branches, stage_labels, stage_colors, stage_icons}]"""

PROCESS_DESCRIPTION_PROMPT = """Describe this business process based on data...
Provide 3-4 sentence business-friendly description."""
```

---

## Faza 6: UI - Mapa procesow i drill-down

### 6.1 Nowy plik: `biai/state/process_map.py` (~100 linii)

```python
class ProcessMapState(rx.State):
    discovered_processes: list[dict] = []  # serializowane DiscoveredProcess
    show_process_map: bool = False
    is_discovering: bool = False
    discovery_error: str = ""
    selected_process_id: str = ""

    @rx.event(background=True)
    async def run_discovery(self): ...  # uruchamia ProcessDiscoveryEngine
```

### 6.2 Nowy plik: `biai/components/process_map_card.py` (~150 linii)

- Grid kart z odkrytymi procesami (nazwa, opis, ikona, badge z liczba stagow)
- Przycisk "Discover Processes" z loading spinner
- Klikniecie karty -> drill-down (process_flow_card z wybranym procesem)
- Error state jesli discovery nie znalazl procesow

### 6.3 Modyfikacja: `biai/components/dashboard_panel.py`

- Dodanie `process_map_card()` nad `process_flow_card()` (widocznosc przez CSS)

---

## Strategia migracji

1. **Feature flag** `USE_DYNAMIC_DISCOVERY` w constants.py - domyslnie `True`
2. **Fallback chain:** discovered > legacy process_training > generic
3. **Stary `process_training.py`** zachowany jako fallback (import warunkowy)
4. **KNOWN_SEQUENCES/KNOWN_BRANCHES** usuwane - zastapione przez `_build_from_discovery()`
5. **STATUS_COLORS/STATUS_ICONS** usuwane natychmiast - DynamicStyler daje identyczne wyniki dla znanych statusow

## Kolejnosc implementacji (minimum viable w kazdej fazie)

| # | Co | Pliki | Wplyw |
|---|-----|-------|-------|
| 1 | DynamicStyler | `dynamic_styler.py` + mod `models/process.py` | Natychmiast usuwa 80 linii hardcoded |
| 2 | Modele discovery | `models/discovery.py` | Fundament |
| 3 | ProcessDiscoveryEngine (heurystyki) | `process_discovery.py` + `process_cache.py` | Odkrywanie z schematu |
| 4 | ProcessDiscoveryEngine (+AI) | mod powyzszego | Nazwy, opisy, kolory z AI |
| 5 | ProcessGraphBuilder refactor | mod `process_graph_builder.py` | Usuwa KNOWN_* |
| 6 | Pipeline integration | mod `pipeline.py` + `process_training_dynamic.py` | Lacznie systemu |
| 7 | UI: ProcessMapState + card | `state/process_map.py` + `components/process_map_card.py` | Wizualna mapa |
| 8 | ProcessDetector dynamic | mod `process_detector.py` | Dynamiczne typy |

## Nowe pliki do stworzenia (8)

| Plik | ~Linii | Opis |
|------|--------|------|
| `biai/ai/dynamic_styler.py` | 100 | Algorytmiczne kolory/ikony |
| `biai/models/discovery.py` | 80 | Modele Pydantic discovery |
| `biai/ai/process_discovery.py` | 300 | Silnik odkrywania procesow |
| `biai/ai/process_cache.py` | 60 | Cache per connection |
| `biai/ai/process_training_dynamic.py` | 120 | Dynamiczny trening Vanna |
| `biai/state/process_map.py` | 100 | Stan mapy procesow (Reflex) |
| `biai/components/process_map_card.py` | 150 | Komponent UI mapy |
| `tests/test_discovery.py` | 200 | Testy discovery + styler |

## Pliki do modyfikacji (7)

| Plik | Zmiany |
|------|--------|
| `biai/models/process.py` | Usun STATUS_COLORS/ICONS, zmien to_react_flow_data() |
| `biai/ai/process_graph_builder.py` | Usun KNOWN_*, dodaj _build_from_discovery(), rozszerz build() |
| `biai/ai/process_detector.py` | Dodaj detect_process_type_dynamic() |
| `biai/ai/pipeline.py` | Integracja discovery w train_schema() i process() |
| `biai/ai/prompt_templates.py` | Nowe prompty discovery |
| `biai/config/constants.py` | Nowe flagi USE_DYNAMIC_DISCOVERY, DISCOVERY_* |
| `biai/components/dashboard_panel.py` | Dodanie process_map_card() |
| `tests/test_process.py` | Aktualizacja testow (DynamicStyler, DiscoveredProcess) |

## Pliki bez zmian (zachowane)

- `biai/ai/process_layout.py` - 100% generyczny (Kahn's toposort)
- `biai/components/react_flow/wrapper.py` - Custom nodes uzywaja data.color/data.icon
- `biai/components/react_flow/process_flow.py` - Komponent React Flow
- `biai/state/process.py` - ProcessState
- `biai/db/schema_manager.py` - SchemaSnapshot z FK
- `biai/db/postgresql.py` / `biai/db/oracle.py` - Konektory

## Weryfikacja

### Testy jednostkowe
```bash
powershell -Command "cd 'E:\PROJECTS\PYTHON_Projects\BIAI'; .\.venv\Scripts\python.exe -m pytest tests/ -v"
```
- Wszystkie 68 istniejacych testow musza przechodzic
- Nowe testy w `tests/test_discovery.py` (~20 testow)
- Zaktualizowane testy w `tests/test_process.py`

### Test integracyjny z Docker DB
```bash
# PostgreSQL test DB (localhost:5433, biai_test)
# Oracle test DB (localhost:1521, XEPDB1)
```
- Polacz sie z test DB
- Uruchom discovery -> sprawdz czy wykrywa ORDER_PROCESS_LOG, SALES_PIPELINE itd.
- Sprawdz czy DynamicStyler daje odpowiednie kolory dla znanych statusow

### Test UI w przegladarce (Chrome DevTools MCP)
- Polacz sie z DB
- Sprawdz czy Process Map card pojawia sie po kliknieciu "Discover"
- Kliknij discovered process -> sprawdz drill-down do process flow
- Zadaj pytanie procesowe w chacie -> sprawdz wizualizacje

# Plan Modernizacji 2026: Dynamiczny Silnik Kontekstu Biznesowego (Oracle/PostgreSQL)

Data: 2026-02-15
Zakres: modernizacja silnika rozpoznawania procesow i mapy biznesowej, z pelnym trybem local-first (Ollama).

## 1. Cel docelowy

Aplikacja ma:
- dzialac niezaleznie od konkretnej bazy (Oracle lub PostgreSQL),
- dynamicznie wykrywac procesy biznesowe na podstawie struktury tabel i opcjonalnie danych,
- budowac nowoczesna, animowana mape procesow i zaleznosci biznesowych,
- pokazywac kontekst biznesowy (znaczenie tabel, relacji, etapow, metryk),
- wykorzystywac lokalne modele LLM (Ollama) przez wyspecjalizowane role.

## 2. Korelacja z obecnym kodem: co zostaje, co zmieniamy

### 2.1 Moduly do zachowania (re-use)

- `biai/db/oracle.py`, `biai/db/postgresql.py`: konektory i snapshot schematu.
- `biai/ai/process_discovery.py`: baza heurystyk discovery.
- `biai/ai/process_graph_builder.py`: generator grafu procesu.
- `biai/ai/process_layout.py`: server-side layout.
- `biai/components/react_flow/*`: nowoczesna warstwa wizualna i animacje.
- `biai/ai/echarts_builder.py`: wykresy pomocnicze (funnel, heatmap, gauge itd.).
- `biai/ai/data_profiler.py` i `biai/ai/business_glossary.py`: dane semantyczne.
- `biai/ai/pipeline.py`: centralny orchestration point.

### 2.2 Krytyczne problemy do naprawy (zmapowane 1:1 do plikow)

1. `biai/ai/process_discovery.py`
- Problem: kandydaci procesu sa budowani glownie z kolumn status/transition; FK-chain nie tworzy samodzielnych kandydatow.
- Skutek: procesy wynikajace glownie z relacji tabel sa pomijane.
- Zmiana: discovery ma byc FK-first + status/transition jako sygnaly wzmacniajace.

2. `biai/ai/process_graph_builder.py`
- Problem: dla danych agregowanych tworzone sa sekwencyjne krawedzie, czesto sztuczne.
- Skutek: diagram pokazuje nieistniejace przeplywy.
- Zmiana: krawedzie tylko z rzeczywistych przejsc (event log / transition matrix), bez "doklejania" liniowych przejsc.

3. `biai/ai/process_detector.py`
- Problem: zbyt agresywna heurystyka pyta procesowych.
- Skutek: falszywe uruchamianie procesowych diagramow.
- Zmiana: detector oparty o scoring wielosygnalowy + prog pewnosci + dowody z SQL/schema/data.

4. `biai/ai/pipeline.py`
- Problem: procesy sa wykrywane post-hoc po wykonaniu query.
- Skutek: brak stabilnego trybu "mapa biznesowa calej bazy".
- Zmiana: osobny etap "Context Discovery Pipeline" uruchamiany po connect/training i cacheowany.

5. `biai/state/chat.py`
- Problem: trening schematu moze failowac cicho, a flaga treningu jest ustawiana.
- Skutek: brak ponownego treningu i nizsza trafnosc.
- Zmiana: jawny status treningu, retry/backoff i blokada ustawiania "trained=true" przy wyjatku.

6. `biai/state/schema.py` (ERD)
- Problem: relacje FK sa rysowane tylko przy prostym dopasowaniu nazwy.
- Skutek: brak czesci krawedzi miedzy tabelami.
- Zmiana: normalizacja identyfikatorow i pelny resolver `schema.table.column`.

7. `biai/state/process_map.py`
- Problem: ID procesu w UI jest nadpisywane indeksem listy.
- Skutek: niestabilny drill-down i utrata tozsamosci procesu.
- Zmiana: uzywac oryginalnego `DiscoveredProcess.id`.

## 3. Architektura docelowa (minimalna zmiana stacku)

### 3.1 Warstwa A: Unified Metadata Graph

Nowy modul:
- `biai/ai/metadata_graph.py`

Funkcja:
- normalizuje metadata z Oracle/PostgreSQL do wspolnego grafu:
  - Node: `table`, `column`, `entity`, `event_candidate`
  - Edge: `fk`, `contains`, `candidate_event_of`, `same_business_term`

Wykorzystuje:
- istniejace snapshoty z konektorow,
- profile (`data_profiler`) i glossary (`business_glossary`).

### 3.2 Warstwa B: Process Discovery 2.0 (schema-first + data-assisted)

Modyfikacje:
- `biai/ai/process_discovery.py` (refactor do pipeline sygnalowego)
- nowy `biai/ai/process_evidence.py` (scoring i dowody)

Mechanizm:
- sygnaly: FK-chain, status columns, transition columns, timestamp columns, cardinality, consistency.
- kazdy proces ma `evidence` + `confidence`.
- wynik musi miec uzasadnienie: "dlaczego ten proces istnieje".

### 3.3 Warstwa C: Event Log Builder (uniwersalny)

Nowy modul:
- `biai/ai/event_log_builder.py`

Funkcja:
- zamienia dane tabel na standard logu zdarzen:
  - `case_id`, `activity`, `ts`, `resource`, `entity_type`.
- obsluguje:
  - tabele historyczne (from/to),
  - tabele statusowe (rekonstrukcja z timestampow),
  - laczenie po FK do encji glownej.

### 3.4 Warstwa D: Business Context Engine

Nowy modul:
- `biai/ai/business_context_engine.py`

Funkcja:
- scala:
  - `metadata_graph`,
  - `discovered_processes`,
  - `profiles`,
  - `glossary`,
  - relacje miedzy procesami i domenami.
- zwraca "Business Map DTO" dla UI (process map + table context + relation context).

### 3.5 Warstwa E: Visualization Orchestrator

Modyfikacje:
- `biai/components/react_flow/process_flow.py`
- `biai/components/process_map_card.py`
- `biai/ai/process_graph_builder.py`
- `biai/ai/echarts_builder.py`

Tryby renderingu:
1. React Flow: glowny diagram procesu (animowane przeplywy, branch, bottleneck).
2. ECharts Sankey: wolumen przeplywow (case flow).
3. ECharts Timeline/Heatmap: czas i obciazenie etapow.
4. Panel kontekstu: opis tabel, FK, semantyka, confidence i evidence.

### 3.6 Warstwa F: Local LLM Orchestration (Ollama role-based)

Nowy modul:
- `biai/ai/llm_orchestrator.py`

Role LLM (lokalne):
- `schema_interpreter`: nazewnictwo biznesowe i aliasy.
- `process_labeler`: etykiety etapow, opis procesu, ikonografia.
- `relationship_explainer`: wyjasnia relacje biznesowe miedzy tabelami/procesami.

Wymagania techniczne:
- tylko structured outputs (JSON) + walidacja Pydantic.
- fallback heurystyczny jesli model nie zwroci poprawnego JSON.
- cache wynikow LLM per `connection_key + schema_hash`.

## 4. Plan wdrozenia etapami

### Etap 0 (Quick Stabilization, 2-4 dni)

- Naprawy krytyczne:
  - `state/chat.py` training status + retry.
  - `state/process_map.py` stabilne ID.
  - `state/schema.py` resolver FK.
  - `process_detector.py` wyzszy prog i lepszy scoring.
- Wynik: mniej falszywych diagramow i poprawna stabilnosc.

### Etap 1 (Discovery Core 2.0, 5-8 dni)

- Implementacja `metadata_graph.py`, `process_evidence.py`.
- Refactor `process_discovery.py` na schema-first.
- Integracja z cache (`process_cache.py`) i `pipeline.train_schema()`.
- Wynik: poprawne wykrywanie procesow dla roznych schematow Oracle/Postgres.

### Etap 2 (Event-Centric Process Graph, 4-7 dni)

- Implementacja `event_log_builder.py`.
- Refactor `process_graph_builder.py`:
  - brak sztucznych sekwencji,
  - tylko krawedzie potwierdzone danymi.
- Wynik: realne, wiarygodne przeplywy.

### Etap 3 (Business Context Map UI, 5-9 dni)

- Implementacja `business_context_engine.py`.
- Rozszerzenie `process_map_card.py` i `process_flow.py`:
  - widok mapa domen/procesow,
  - animowane przeplywy + panel relacji tabel.
- Rozszerzenie `echarts_builder.py` o produkcyjny `SANKEY` i `TIMELINE`.
- Wynik: nowoczesna dynamiczna mapa biznesowa.

### Etap 4 (LLM Role Orchestration, 4-6 dni)

- `llm_orchestrator.py` + nowe prompty rolowe.
- Uzycie lokalnych modeli Ollama per zadanie (bez cloud dependency).
- Structured output contracts i walidacja.
- Wynik: lepszy kontekst biznesowy bez utraty local-first.

### Etap 5 (QA + Benchmark, 3-5 dni)

- Testy:
  - `tests/test_discovery.py` (precision/recall discovery),
  - `tests/test_process.py` (trafnosc grafu),
  - nowe testy integracyjne Oracle/Postgres na seedach.
- Metryki akceptacyjne:
  - Precision discovery >= 0.85
  - Recall discovery >= 0.80
  - Accuracy krawedzi przeplywu >= 0.90
  - TTFD (first process map) <= 8s dla sredniego schematu (<=80 tabel)

## 5. Biblioteki: co zostaje, co rozszerzamy

Zostaje:
- Reflex, React Flow wrapper, ECharts wrapper, Vanna + Chroma, sqlglot, pandas.

Rozszerzenia rekomendowane:
- `networkx` (graf relacji i topologia procesu),
- `rapidfuzz` (fuzzy matching nazw biznesowych i synonymy),
- opcjonalnie `pm4py` (zaawansowane metryki process mining, jesli potrzebne conformance/variant analysis).

Uwaga:
- Nie zmieniamy fundamentu UI ani connectorow.
- Modernizacja jest ewolucyjna, bez przepisywania aplikacji od zera.

## 6. Definicja "done" dla celu biznesowego

Modernizacja jest zakonczona, gdy:
- po podlaczeniu do dowolnej bazy Oracle/PostgreSQL aplikacja sama tworzy mape procesow,
- mapa pokazuje poprawne przeplywy i relacje tabel (nie sekwencje sztuczne),
- kazdy proces ma confidence + evidence + opis biznesowy,
- UI oferuje animowany widok procesowy + widok sankey/timeline,
- wszystko dziala na lokalnych modelach Ollama (bez wymagania cloud).

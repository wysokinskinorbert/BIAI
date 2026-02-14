# BIAI - Kompleksowa Analiza UI/UX

**Data:** 2026-02-13 (Q1-Q20), 2026-02-14 (Q21-Q30)
**Metoda:** 30 zapytan testowych pokrywajacych wszystkie typy wizualizacji, multi-step analysis, edge cases
**Screenshoty:** `docs/ui_analysis/q01-q20`, `docs/ui_analysis/q21-q30`

---

## 1. Podsumowanie Wykonawcze

Aplikacja BIAI poprawnie realizuje podstawowy flow: pytanie -> SQL -> dane -> wizualizacja.
Jednak warstwa prezentacji danych wymaga istotnych usprawnien, aby system mogl byc uznany
za profesjonalne narzedzie BI. Glowne problemy dotycza:

- **Layout Process Flow** - wezly ukladaja sie w pionowa kolumne zamiast wykorzystywac
  dostepna przestrzen horyzontalnie (POPRAWIONE w Q21-Q30: layout LR dziala!)
- **Dobor typow wykresow** - chart advisor nie rozpoznaje niektorych wzorcow danych
  (np. dane procentowe -> bar zamiast pie)
- **Brak dynamicznego skalowania** - stale wysokosci wykresow (350px) i process flow (400px)
  nie dostosowuja sie do zlozonosci danych
- **Brak kluczowych komponentow BI** - karty KPI, heatmapy, drill-down, multi-dashboard

**NOWE (Q21-Q30) - krytyczne problemy pipeline'u:**
- **Multi-step analysis context contamination** - planner re-wykonuje zapytania z poprzednich
  tur rozmowy zamiast generowac nowe (Q28)
- **AI halucynacje** - opis wynikow oparty na danych z INNEGO zapytania (Q28, Q30)
- **LIMIT ignorowany** - SQL ma LIMIT 5, ale wynik to 447 wierszy (Q27)
- **Dashboard state inconsistency** - tytul z Q26, dane z Q27, Process Flow z Q26 (Q27-Q30)
- **Analysis Steps globalny stan** - steps z Q30 wyswietlane pod wiadomoscia Q28

---

## 2. Problemy Krytyczne (CRITICAL)

### 2.1 Process Flow - wezly w pionowej kolumnie

**Dotyczy:** Q1, Q5, Q6, Q9, Q12, Q13, Q16, Q20
**Plik:** `biai/ai/process_layout.py`

**Problem:** Algorytm `calculate_layout()` uzywa Kahn's topological sort, ktory dla
lancuchow procesowych (A->B->C->D->E) tworzy osobna warstwe dla kazdego wezla.
Kazda warstwa ma 1 wezel, wiec wszystkie wezly laduja w jednej kolumnie pionowej.

**Efekt wizualny:**
- 7-9 wezlow ulozone jeden pod drugim w waskiej kolumnie
- 70-80% kontenerze to pusta przestrzen po prawej stronie
- `fit_view=True` zoomuje, ale proporcje sa zle (wysoki waski graf w szerokim kontenerze)

**Sugerowane rozwiazanie:**
1. Dla prostych lancuchow (max 1 wezel na warstwe) -> przelacz na layout horyzontalny (LR)
2. Adaptacyjny layout: jesli stosunek wysokosc/szerokosc > 2.0 -> uzyj LR zamiast TB
3. Rozwazyc uzycie biblioteki Dagre.js po stronie klienta zamiast server-side layout

```python
# process_layout.py - adaptacyjny layout
def calculate_layout(nodes, edges, direction="TB", ...):
    # ... existing Kahn's algorithm ...

    # Adaptive: if graph is too tall/narrow, switch to LR
    max_layer_width = max(len(layer) for layer in layers) if layers else 1
    num_layers = len(layers)
    if direction == "TB" and max_layer_width == 1 and num_layers > 3:
        return calculate_layout(nodes, edges, direction="LR", ...)
```

### 2.2 Dashboard nie skaluje sie dynamicznie

**Dotyczy:** Wszystkie zapytania
**Pliki:** `biai/components/chart_card.py`, `biai/components/react_flow/process_flow.py`

**Problem:**
- Wykres ECharts: stale `height="350px"` (linia 46 chart_card.py)
- Process Flow: stale `height="400px"` (linia 107 process_flow.py)
- Fullscreen dialog: stale `height="500px"` (linia 94 chart_card.py)

**Efekt:**
- Dla 3 kategorii (pie chart) - 350px to za duzo, pusta przestrzen
- Dla 20+ kategorii (bar chart) - 350px to za malo, etykiety nachodza
- Process flow z 3 wezlami marnuje 300px pustej przestrzeni
- Process flow z 10 wezlami jest scisniety

**Sugerowane rozwiazanie:**
1. Dynamiczna wysokosc oparta na liczbie elementow danych
2. Uzycie CSS `min-height`/`max-height` zamiast `height`
3. Wykres: `min(350, max(200, rows * 35))px`
4. Process: `min(500, max(250, nodes * 50))px`

### 2.3 Bledny dobor typow wykresow

**Dotyczy:** Q3 (pie -> bar), Q17 (single value -> bar)
**Plik:** `biai/ai/chart_advisor.py`

**Problem A - Q3:** Zapytanie o "procentowy udzial" powinno dac PIE chart, dostaje BAR.
Heurystyka nie wykrywa slow kluczowych: "procentowy", "udzial", "rozklad", "dystrybucja",
"share", "proportion", "distribution", "percentage".

**Problem B - Q17:** Pojedyncza wartosc (1 produkt) renderuje sie jako jeden bar w calym
wykresie - wyglada dziwnie i nieczytelnie.

**Sugerowane rozwiazanie A:**
```python
# chart_advisor.py - dodac do heurystyki
pie_keywords = ["pie", "percentage", "proportion", "share", "distribution",
                "procentowy", "udzial", "rozklad", "dystrybucja"]
if any(kw in question_lower for kw in pie_keywords) and len(cat_cols) >= 1:
    return ChartConfig(chart_type=ChartType.PIE, ...)
```

**Sugerowane rozwiazanie B:**
```python
# chart_advisor.py - dodac na poczatku heurystyki
if len(df) == 1 and len(num_cols) >= 1:
    return ChartConfig(chart_type=ChartType.TABLE)  # lub KPI card
```

---

## 3. Problemy Wysokie (HIGH)

### 3.1 Zbyt wiele kategorii na bar chart - etykiety nachodza

**Dotyczy:** Q7 (20+ bars - tickety po kategorii i priorytecie)
**Plik:** `biai/ai/echarts_builder.py`

**Problem:** Dla wiecej niz ~10 kategorii, slupki sa bardzo waskie, a etykiety osi X
nachodza na siebie nawet z `rotate: 30`.

**Sugerowane rozwiazanie:**
1. >10 kategorii -> horyzontalne slupki (zamiana xAxis/yAxis)
2. >15 kategorii -> TOP N z adnotacja "i X pozostalych"
3. Dodanie `axisLabel.interval: 0` + `rotate: 45` + `grid.bottom: "25%"`

### 3.2 Brak etykiet wartosci na slupkach

**Dotyczy:** Wszystkie wykresy barowe
**Plik:** `biai/ai/echarts_builder.py`

**Problem:** Slupki nie wyswietlaja wartosci numerycznych. Uzytkownik musi "zgadywac"
wartosci z osi Y lub najezdzac myszka (tooltip).

**Sugerowane rozwiazanie:**
```python
# echarts_builder.py - dodac do kazdej serii
"label": {
    "show": True,
    "position": "top",
    "color": "#ccc",
    "fontSize": 11,
}
```

### 3.3 Brak grupowanych/skumulowanych wykresow

**Dotyczy:** Q7 (kategoria x priorytet), Q18 (anulowane vs dostarczone)
**Plik:** `biai/ai/echarts_builder.py`, `biai/ai/chart_advisor.py`

**Problem:** Dane z dwoma wymiarami kategorycznymi (np. kategoria x priorytet)
renderuja sie jako flat bar chart z N*M slupkami zamiast grouped bars.

**Sugerowane rozwiazanie:**
1. ChartAdvisor wykrywa 2 kolumny kategoryczne -> GROUPED_BAR
2. ECharts builder tworzy osobna serie dla kazdej kategorii drugorzedenj
3. Dodac `ChartType.STACKED_BAR` i `ChartType.GROUPED_BAR`

### 3.4 Tytuły wykresow obcinane

**Dotyczy:** Q2, Q5, Q8, Q12, Q20
**Plik:** `biai/components/chart_card.py`, `biai/ai/echarts_builder.py`

**Problem:** Dlugie tytuly sa obcinane w naglowku karty i w samym wykresie ECharts.

**Sugerowane rozwiazanie:**
1. `text-overflow: ellipsis` + tooltip na hover w naglowku karty
2. ECharts title: `textStyle.overflow: "truncate"` + `width: "80%"`
3. Alternatywnie: krotszy tytul + pelny w tooltip

### 3.5 Self-correction widoczna jako "Attempt 3" bez kontekstu

**Dotyczy:** Q5, Q14, Q16
**Pliki:** `biai/components/sql_viewer.py`

**Problem:** Badge "Attempt 3" na SQL viewer nie informuje uzytkownika co sie stalo.
Brak informacji o bledach poprzednich prob i co zostalo poprawione.

**Sugerowane rozwiazanie:**
1. Tooltip na "Attempt N" z krotkim opisem bledow
2. Opcjonalny rozwijany panel z historia prob

---

## 4. Problemy Srednie (MEDIUM)

### 4.1 Tabela danych za mala dla wielu kolumn

**Dotyczy:** Q11 (klienci - 4 kolumny), Q7 (2 kolumny + duzo wierszy)
**Problem:** Tabela nie ma horyzontalnego scrollowania, kolumny sie zginaja.
**Rozwiazanie:** `overflow-x: auto` na kontenerze tabeli + `min-width` na kolumnach.

### 4.2 Brak paginacji dla duzych tabel

**Dotyczy:** Q11 (100 klientow), Q7 (20+ wierszy)
**Problem:** Wszystkie wiersze renderowane naraz, wymuszajac dlugie scrollowanie.
**Rozwiazanie:** Paginacja co 10-20 wierszy z przyciskami nawigacji.

### 4.3 Sekcja SQL zajmuje zbyt duzo miejsca

**Dotyczy:** Wszystkie zapytania
**Problem:** SQL viewer jest domyslnie rozwiniety i zajmuje ~200px na dashboard.
Dla prostych zapytan (1 linia SQL) to marnotrawstwo.
**Rozwiazanie:** Domyslnie zwiniety (collapsed) z przyciskiem "Show SQL".

### 4.4 Komunikaty bledow mato widoczne

**Dotyczy:** Q14, Q16
**Problem:** Czerwony tekst bledu w chat jest maly i wtapia sie w reszte wiadomosci.
**Rozwiazanie:** Wyrazna karta bledu z ikona, kolorem tla, i przyciskiem "Retry".

### 4.5 Staly podzial 40/60 Chat/Dashboard

**Dotyczy:** Wszystkie widoki
**Problem:** Proporcja nie dostosowuje sie do zawartosci. Przy dlugich odpowiedziach
chat jest za ciasny. Przy prostych danych dashboard ma za duzo pustej przestrzeni.
**Rozwiazanie:** Przesuwany separator (drag-to-resize) lub toggle full-width dashboard.

---

## 5. Problemy Niskie (LOW)

### 5.1 Niespojne kolory miedzy wykresami

Rozne zapytania uzywaja roznych palet kolorow. Bar chart ma niebieski, kolejny zielony+zolty.
**Rozwiazanie:** Stala paleta zdefiniowana w design tokens.

### 5.2 Mala/brakujaca legenda na multi-series charts

**Dotyczy:** Q18 (2 linie - cancelled vs delivered)
**Rozwiazanie:** `legend.show: true` w ECharts option z czytelna pozycja.

### 5.3 Brak animacji ladowania

Kiedy AI przetwarza pytanie, dashboard stoi pusty lub pokazuje stare dane.
**Rozwiazanie:** Skeleton loader na dashboard podczas generowania odpowiedzi.

---

## 6. Brakujace Funkcjonalnosci (Gap Analysis)

### 6.1 PRIORYTET WYSOKI - Kluczowe dla profesjonalnego BI

| # | Funkcjonalnosc | Opis | Zlozonosc |
|---|----------------|------|-----------|
| F1 | **Karty KPI** | Pojedyncze metryki (total revenue, count, avg) jako duze karty z ikona, wartosc, trend | Srednia |
| F2 | **Drill-down** | Klikniecie slupka/segmentu pie filtruje dane i pokazuje szczegoly | Wysoka |
| F3 | **Horizontal bar chart** | Automatyczny switch na poziome slupki dla >10 kategorii | Niska |
| F4 | **Grouped/Stacked bars** | Wykres z grupowanymi slupkami dla 2-wymiarowych danych | Srednia |
| F5 | **Adaptive layout** | Dynamiczna wysokosc komponentow na podstawie danych | Srednia |
| F6 | **Process Flow LR layout** | Horyzontalny layout dla lancuchow procesow | Niska |
| F7 | **Pie chart detection** | Lepsza heurystyka rozpoznawania danych procentowych | Niska |

### 6.2 PRIORYTET SREDNI - Rozszerzenia

| # | Funkcjonalnosc | Opis | Zlozonosc |
|---|----------------|------|-----------|
| F8 | **Multi-query Dashboard** | Pinowanie wielu wynikow na jednym dashboardzie | Wysoka |
| F9 | **Saved Queries** | Zapisywanie ulubionych zapytan z mozliwoscia ponownego uruchomienia | Srednia |
| F10 | **Data Filtering** | Filtrowanie/sortowanie w tabeli wynikow bez nowego zapytania | Srednia |
| F11 | **Heatmap** | Dla danych 2D (np. tickety per kategoria per priorytet) | Srednia |
| F12 | **Gauge chart** | Dla KPI z targetem (np. % realizacji celu sprzedazy) | Niska |
| F13 | **Treemap** | Dla danych hierarchicznych (region -> miasto -> klienci) | Srednia |
| F14 | **Sankey diagram** | Dla flow danych (np. order status transitions z wolumenem) | Wysoka |
| F15 | **Waterfall chart** | Dla danych finansowych (revenue breakdown) | Srednia |

### 6.3 PRIORYTET NISKI - Polish

| # | Funkcjonalnosc | Opis | Zlozonosc |
|---|----------------|------|-----------|
| F16 | **Chart annotations** | Mozliwosc dodawania notatek do wykresow | Srednia |
| F17 | **Dark/Light theme toggle** | Pelne wsparcie motywu jasnego | Srednia |
| F18 | **Responsive layout** | Dostosowanie do roznych rozmiarow ekranu | Wysoka |
| F19 | **Chart export** | Eksport wykresow jako PNG/SVG/PDF | Niska |
| F20 | **Dashboard templates** | Predefiniowane uklady dla roznych typow analiz | Wysoka |

---

## 7. Rekomendacja: Plan Implementacji Usprawnien

### Faza 1: Quick Wins (1-2 dni)

1. **F6 - Process Flow LR layout** - zmiana `direction="LR"` w `calculate_layout()`
   gdy graf jest lancuchem (max 1 wezel na warstwe)
2. **F7 - Pie chart detection** - dodanie keywords: "procentowy", "udzial", "distribution"
3. **F3 - Horizontal bars** - switch na horizontal gdy `len(x_data) > 10`
4. **Etykiety wartosci na slupkach** - `label.show: true` w ECharts builder
5. **SQL viewer domyslnie zwiniety** - `collapsed=True` default

### Faza 2: Layout & Scaling (3-5 dni)

1. **F5 - Adaptive layout** - dynamiczna wysokosc wykresow i process flow
2. **Resizable split** - drag-to-resize separator chat/dashboard
3. **Lepsze tooltips** - tytuly, attempt badge, metryki
4. **Paginacja tabeli** - przyciskami co 15 wierszy
5. **Skeleton loaders** - podczas ladowania danych

### Faza 3: Nowe Typy Wizualizacji (5-8 dni)

1. **F1 - Karty KPI** - nowy komponent `kpi_card.py` dla single-value wynikow
2. **F4 - Grouped/Stacked bars** - nowy typ w ChartAdvisor + ECharts builder
3. **F11 - Heatmap** - ECharts heatmap dla 2D danych
4. **F12 - Gauge chart** - ECharts gauge dla KPI z targetami
5. **F15 - Waterfall chart** - ECharts waterfall dla finansow

### Faza 4: Zaawansowane BI (10+ dni)

1. **F2 - Drill-down** - klikniecie elementu wykresu generuje follow-up query
2. **F8 - Multi-query Dashboard** - pinowanie wielu wynikow
3. **F9 - Saved Queries** - localStorage/DB persystencja ulubionych
4. **F14 - Sankey diagram** - dla flow danych procesowych
5. **F10 - Data Filtering** - interaktywne filtry na tabeli

---

## 8. Szczegolowa Analiza Poszczegolnych Zapytan

### Q1: Zamowienia wg statusu (Bar + Process Flow)
- **Wykres:** Bar chart z 5 slupkami - OK
- **Process Flow:** 5 wezlow w pionowej kolumnie, pusta przestrzen po prawej
- **Problem:** Layout TB dla lancucha A->B->C->D->E

### Q2: Trend miesieczny (Line chart)
- **Wykres:** Line chart 12 punktow - OK
- **Problem:** Tytul obciety na karcie dashboard

### Q3: Tickety wg priorytetu (blednie Bar zamiast Pie)
- **Wykres:** Bar chart z 4 slupkami (P1-P4 z procentami)
- **Problem:** Powinnien byc PIE chart - dane procentowe

### Q4: Top 10 klientow (Bar chart)
- **Wykres:** Bar chart z 10 slupkami - OK
- **Problem:** Brak etykiet wartosci, dlugie nazwiska na osi X

### Q5: Sredni czas etapow procesu (Bar + Process Flow)
- **Wykres:** Bar chart z 7 etapami - OK
- **Process Flow:** 7 wezlow w pionie, duza pusta przestrzen
- **Problem:** SQL potrzebowal 3 proby (Attempt 3)

### Q6: Lejek sprzedazy (Bar + Process Flow)
- **Wykres:** Bar chart etapow pipeline - OK
- **Process Flow:** Wezly w pionie
- **Problem:** Lejek powinnien byc wizualizowany jako funnel chart

### Q7: Tickety wg kategorii i priorytetu (Bar chart)
- **Wykres:** 20+ cienkich slupkow
- **Problem:** Za duzo kategorii, etykiety nachodza. Potrzebne grouped bars lub heatmap

### Q8: Miesieczna wartosc sprzedazy (Line chart)
- **Wykres:** Line chart z 12 punktami - OK
- **Problem:** Brak data labels na punktach

### Q9: Approval process flow (Bar + Process)
- **Wykres:** Bar chart statusow - OK
- **Process Flow:** Wezly w pionie
- **Problem:** Taki sam jak Q1/Q5/Q6

### Q10: Top 5 pracownikow (Bar chart)
- **Wykres:** Bar chart z 5 slupkami - OK
- **Problem:** Zielone + zolte slupki - niespojne z reszta

### Q11: Tabela klientow (Table)
- **Tabela:** 100 wierszy x 4 kolumny
- **Problem:** Brak paginacji, tabela wymaga duzego scrollowania

### Q12: Srednia wartosc deali w pipeline (Bar + Process)
- **Wykres:** Bar chart etapow - OK
- **Process Flow:** Wezly w pionie
- **Problem:** Layout + pusta przestrzen

### Q13: Ticket process flow
- **Process Flow:** Wezly w pionie z bottleneck
- **Problem:** Identyczny layout issue

### Q14: Zamowienia wg regionu (Bar chart)
- **Wykres:** Bar chart z regionami - OK
- **Problem:** Self-correction (bledy kolumn), ale finalnie poprawne

### Q15: Wynagrodzenia wg dzialow (Bar chart)
- **Wykres:** Bar chart z 7 dzialami - OK
- **Problem:** Brak data labels

### Q16: Pipeline history flow
- **Problem:** AI nie moglo wygenerowac poprawnego SQL (bledy kolumn)
- **Stale dane:** Dashboard pokazuje stare dane z Q15

### Q17: Top 10 produktow (Bar chart)
- **Wykres:** Jeden slupek dominuje (1 produkt)
- **Problem:** Powinno byc wiecej produktow, AI zwrocilo tylko 1

### Q18: Anulowane vs dostarczone (Multi-line)
- **Wykres:** 2 linie (cancelled, delivered) - OK
- **Problem:** Legenda mala, brak rozroznienia serii

### Q19: Czas rozwiazania wg priorytetu (Bar chart)
- **Wykres:** 4 slupki priorytetow - OK
- **Problem:** Brak data labels

### Q20: Pelny proces zamowienia (Bar + Process Flow)
- **Wykres:** Bar chart z etapami
- **Process Flow:** Wezly w pionie
- **Problem:** Layout + brak czasu na krawedziach (mimo ze dane sa w wyniku)

---

## 9. Heurystyki Nielsena - Ocena

| # | Heurystyka | Ocena (1-5) | Uwagi |
|---|-----------|-------------|-------|
| H1 | Widocznosc statusu systemu | 3/5 | Brak skeleton loadera, ale streaming text widoczny |
| H2 | Dopasowanie do swiata | 4/5 | Dobre nazewnictwo, zrozumiale etykiety |
| H3 | Kontrola uzytkownika | 2/5 | Brak undo, brak resize, brak drag-to-reorder |
| H4 | Spojnosc | 3/5 | Niespojne kolory, mieszanka stylów kart |
| H5 | Zapobieganie bledom | 3/5 | Self-correction dziala, ale bledy nieczytelne |
| H6 | Rozpoznawanie zamiast pamieci | 3/5 | Brak suggested queries, brak historii |
| H7 | Elastycznosc | 2/5 | Brak skrotow, brak customizacji layoutu |
| H8 | Minimalizm | 3/5 | SQL viewer domyslnie rozwiniety to szum |
| H9 | Pomoc w naprawie bledow | 3/5 | Self-correction OK, ale komunikaty mgliste |
| H10 | Dokumentacja | 2/5 | Brak tooltipow, brak onboarding, brak help |

**Srednia:** 2.8/5

---

---

## 10. Wyniki Testow Q21-Q30 (2026-02-14)

### 10.1 Nowe Problemy Krytyczne

#### 10.1.1 Multi-step analysis context contamination (CRITICAL)

**Dotyczy:** Q28
**Pliki:** `biai/ai/analysis_planner.py`, `biai/ai/pipeline.py`

**Problem:** AnalysisPlanner otrzymuje kontekst rozmowy i generuje kroki na bazie
POPRZEDNICH zapytan zamiast BIEZACEGO. Q28 ("handlowiec z najlepsza konwersja") dostal
plan: Step 1 = "Find orders without process log entries" (to Q26!), Step 2 = "Filter
sales_pipeline for closed_won" (to dopiero Q28). Step 2 failed, wiec pipeline zwrocil
dane z Step 1 = Q26 dane.

**Efekt:** Odpowiedz na Q28 to dane z Q26. AI halucynuje opis na bazie Q26 danych.

**Sugerowane rozwiazanie:**
1. Wyczysc kontekst rozmowy przed planowaniem multi-step (nie przekazuj ctx do planner)
2. Waliduj kroki: kazdy step musi byc semantycznie powiazany z pytaniem
3. Jesli Step 1 pokrywa sie z ostatnim zapytaniem, pomin go

#### 10.1.2 LIMIT ignorowany w wynikach (CRITICAL)

**Dotyczy:** Q27
**Pliki:** `biai/ai/sql_validator.py`, `biai/db/query_executor.py`

**Problem:** SQL: `...ORDER BY ticket_count DESC LIMIT 5` ale Results: 447 wierszy.
Mozliwe przyczyny: (a) sqlglot transpilation usunela LIMIT, (b) validator zmienil SQL,
(c) inny SQL zostal wykonany niz wyswietlony.

**Sugerowane rozwiazanie:**
1. Logowac finalne SQL po walidacji/transpilacji
2. Porownac SQL w Generated SQL z faktycznie wykonanym
3. Sprawdzic czy sqlglot transpilation zachowuje LIMIT

#### 10.1.3 Type comparison error w pipeline (CRITICAL)

**Dotyczy:** Q27
**Pliki:** `biai/ai/chart_advisor.py` lub `biai/ai/insight_agent.py`

**Problem:** `'<' not supported between instances of 'str' and 'float'` - blad
porownania typow w post-processingu (chart advisor lub insight generation).
Dane z multi-JOIN zawieraja mieszane typy kolumn.

**Sugerowane rozwiazanie:**
1. Dodac `try/except TypeError` w chart_advisor.recommend()
2. Wymuszac numeryczne typy: `df[col] = pd.to_numeric(df[col], errors='coerce')`
3. Testy: multi-JOIN z mieszanymi typami kolumn

#### 10.1.4 AI halucynacje oparte na danych z innego zapytania (CRITICAL)

**Dotyczy:** Q28, Q30
**Pliki:** `biai/ai/pipeline.py`, `biai/state/chat.py`

**Problem:** AI opis Q28 mowi o "order IDs from 10 to 500, averaging 304.56" = dane z Q26.
Q30 mowi o "no variation between min, max, avg of 250" = bezsensowne dla COUNT.
Pipeline uzywa `_extract_key_points(df)` z niewlasciwego DataFrame.

### 10.2 Nowe Problemy Wysokie (HIGH)

#### 10.2.1 Dashboard state inconsistency

**Dotyczy:** Q27, Q28, Q29, Q30

**Problem:** Po bledzie lub multi-step analysis:
- Tytul dashboardu z Q26
- Dane w Results z Q27 (lub stale Q26 przy bledzie)
- Process Flow z Q26
- Follow-up suggestions z Q26

Dashboard nie czyści stanu po nowym zapytaniu jesli ono bleduje.

#### 10.2.2 Analysis Steps globalny stan zamiast per-message

**Dotyczy:** Q28, Q30
**Pliki:** `biai/state/chat.py`, `biai/components/chat_message.py`

**Problem:** `ChatState.analysis_steps` to globalny var. Kiedy Q30 aktualizuje steps,
WSZYSTKIE wiadomosci z `is_multi_step=True` pokazuja Q30 steps - nawet Q28.
Powinno byc per-message (jak `insights` po poprawce z Phase 2).

**Sugerowane rozwiazanie:** Przeniesc `analysis_steps` do `message["analysis_steps"]`
analogicznie do poprawki `insights` z commitu d7f872d.

#### 10.2.3 SQL section nie rozwijalna (Q22)

**Dotyczy:** Q22
**Problem:** Klikniecie "Generated SQL" w dashboardzie nie rozwija sekcji SQL.
Uzytkownik nie moze zobaczyc wygenerowanego zapytania.

#### 10.2.4 Bledne obliczenia procentowe

**Dotyczy:** Q22, Q24, Q30
**Problem:**
- Q22: "Ile % wnioskow odrzucanych?" → wynik "0E-20" zamiast ~13.5% (27/200)
- Q24: "Typ wniosku z najwyzszym odrzuceniem" → 0 wierszy (powinny byc dane)
- Q30: "% reopened ticketow" → 250 (total count zamiast procentu)

AI nie umie obliczac procentow w jednym zapytaniu SQL. Potrzebne wzorce:
`COUNT(CASE WHEN status='rejected' THEN 1 END) * 100.0 / COUNT(*)`

### 10.3 Nowe Problemy Srednie (MEDIUM)

- **Follow-up suggestions z poprzedniego zapytania** (Q27-Q30)
- **Error pokazuje tylko Attempt 4-5** nie wszystkie proby (Q23, Q29)
- **Dashboard stale dane po bledzie** - nie czyści się (Q29)
- **Brak "0 rows" badge** przy pustych wynikach (Q24)
- **Liczby bez separatorow tysiecy** na pie chart (Q25)
- **Key Metric wyswietla zly typ** - COUNT zamiast % (Q30)

### 10.4 Pozytywne Obserwacje (Q21-Q30)

1. **Process Flow layout LR** - teraz horyzontalny! Poprawka z Phase 4 dziala (Q26)
2. **PIE chart poprawnie wybrany** dla "rozklad kwot" (Q25) - heurystyka "rozklad" dziala
3. **Per-message Insights** - insights wyswietlane per wiadomosc (poprawka d7f872d)
4. **LEFT JOIN + NULL** - AI poprawnie uzywa tego wzorca (Q26)
5. **Key Metric component** - ladny duzy numer dla single-value wynikow (Q30)
6. **Retry button** - poprawnie wyswietlany przy bledach
7. **Paginacja** - dziala dla duzych zbiorow (Q26: 1/26, Q27: 1/30)

---

## 11. Szczegolowa Analiza Q21-Q30

### Q21: "Jaki jest trend liczby nowych ticketow miesiecznie?"
- **Wynik:** Line chart, 5 wierszy (5 miesiecy z danymi)
- **Wykres:** Liniowy z adnotacjami markPoint/markLine
- **Problemy:**
  - Os X pokazuje "2024.0" (float zamiast formatu daty/miesiaca)
  - Tylko 5 miesiecy z danymi (seed data ograniczone)
  - Tytul wyklesu obciety
  - Adnotacje markPoint nachodza na siebie

### Q22: "Ile procent wnioskow jest odrzucanych?"
- **Wynik:** Key Metric "0E-20" (notacja naukowa!)
- **SQL:** Zly wzorzec - nie uzywa COUNT(CASE WHEN...) * 100.0 / COUNT(*)
- **Problemy CRITICAL:**
  - Wartosc "0E-20" zamiast ~13.5% (27/200 rejected)
  - Brak aliasu kolumny ("?column?")
  - Sekcja "Generated SQL" nie rozwijalna (BUG UI)
  - Brak przycisku "Add to Dashboard Builder"

### Q23: "Pokaz korelacje miedzy wartoscia zamowienia a czasem realizacji"
- **Wynik:** ERROR po 5 probach
- **Blad:** `column "updated_at"/"resolved_at" does not exist`
- **Problemy:**
  - AI myli kolumny miedzy tabelami
  - Dashboard fallback do Database Schema
  - Follow-up wyswietlane po bledzie
  - Error pokazuje tylko Attempt 4-5

### Q24: "Ktory typ wniosku ma najwyzszy wskaznik odrzucen?"
- **Wynik:** 0 wierszy (powinny byc dane)
- **SQL:** Ten sam problem co Q22 - bledny wzorzec procentowy
- **Problemy:**
  - Dashboard fallback do Schema
  - Follow-up po pustych wynikach
  - Brak badge "0 rows"

### Q25: "Pokaz rozklad kwot wnioskow po typach"
- **Wynik:** SUCCESS - PIE chart, 5 wierszy
- **Wykres:** Pie chart poprawnie wybrany (keyword "rozklad")
- **Problemy:**
  - Liczby bez separatorow tysiecy
  - Legenda nachodzi na etykiety
  - Brak procentow na label pie
- **POZYTYWNE:** PIE chart poprawnie dobrany!

### Q26: "Ile zamowien nie ma zadnych wpisow w process log?"
- **Wynik:** SUCCESS - 380 wierszy, LEFT JOIN + IS NULL
- **Problemy:**
  - Process Flow wykryty ale semantycznie bledny (pytanie o BRAK procesow)
  - Insights na order_id PK bezsensowne (upward trend +4900%)
  - Pytanie "ile" powinno zwrocic COUNT, nie liste
- **POZYTYWNE:** Process Flow layout HORYZONTALNY! Paginacja 1/26 dziala!

### Q27: "Pokaz top 5 klientow z najwieksza liczba ticketow i ich laczna wartosc zamowien"
- **Wynik:** ERROR - `'<' not supported between instances of 'str' and 'float'`
- **SQL:** `...ORDER BY ticket_count DESC LIMIT 5` ale wynik 447 wierszy
- **Problemy CRITICAL:**
  - LIMIT 5 zignorowany (447 rows)
  - Brak kolumny "total order value" (SQL nie laczy z orders)
  - Type comparison error w post-processingu
  - Dashboard tytul z Q26, dane z Q27
  - Process Flow z Q26 nadal wyswietlany

### Q28: "Ktory handlowiec ma najlepsza konwersje closed_won?"
- **Wynik:** Multi-step analysis - Step 1 = Q26 query (!), Step 2 = failed
- **Problemy CRITICAL:**
  - Context contamination: Step 1 re-wykonuje Q26
  - HALUCYNACJA: opis mowi o "order IDs 10-500, avg 304.56" (Q26 dane)
  - Dashboard: 380 rows order_id = Q26 dane
  - Step 2 (wlasciwy krok) FAILED

### Q29: "Pokaz liczbe zamowien, ticketow i wnioskow miesiecznie"
- **Wynik:** ERROR po 5 probach
- **Blad:** `column "ticket_id" does not exist` (x5)
- **Problemy:**
  - Self-correction nie poprawia - 5x ten sam blad
  - Brak kolumny ticket_id (powinno byc id w support_tickets)
  - Dashboard stale dane Q26

### Q30: "Jaki procent ticketow jest ponownie otwieranych?"
- **Wynik:** Multi-step: Step 1 = 0 reopened, Step 2 = COUNT(*) = 250
- **Dashboard:** Key Metric "250", SQL: `SELECT COUNT(*) FROM support_tickets`
- **Problemy:**
  - Odpowiedz to COUNT, nie procent (powinno: "0%")
  - Opis AI bezsensowny ("no variation between min, max, avg")
  - Analysis Steps z Q30 pod wiadomoscia Q28 (globalny stan)
  - Brak Step 3: "Calculate percentage"

---

## 12. Podsumowanie Statystyczne Q1-Q30

| Metryka | Q1-Q20 | Q21-Q30 | Lacznie |
|---------|--------|---------|---------|
| Zapytan | 20 | 10 | 30 |
| Sukces (poprawne dane) | 16 | 3 (Q25, Q26, Q30*) | 19 |
| Bledne dane | 2 | 3 (Q22, Q24, Q27) | 5 |
| Error (brak wynikow) | 2 | 4 (Q23, Q27, Q28, Q29) | 6 |
| Multi-step triggered | 0 | 3 (Q28, Q30, partial Q29) | 3 |
| Multi-step poprawny | 0 | 0 | 0 |

*Q30 technicznie sukces (dane zwrocone), ale nie odpowiada na pytanie

### Rozklad problemow wg severity (Q21-Q30)

| Severity | Ilosc | Opis |
|----------|-------|------|
| CRITICAL | 5 | Context contamination, LIMIT ignored, type error, hallucination, wrong percentage |
| HIGH | 6 | Dashboard inconsistency, global analysis_steps, SQL section, percentage patterns |
| MEDIUM | 6 | Follow-up stale, error truncated, stale dashboard, 0-rows badge, separators, Key Metric |
| LOW | 3 | React Hooks warning, ECharts DOM, pie legend overlap |

---

## 13. Zaktualizowane Podsumowanie

Aplikacja BIAI ma solidny backend (pipeline AI, SQL validation, self-correction) i dobrze
realizuje podstawowy flow konwersacyjny. Glowne wyzwania leza w **warstwie prezentacji**
oraz **pipeline multi-step analysis**:

### Pilne poprawki (Q21-Q30 findings):

1. **Multi-step analysis planner** - context contamination to showstopper; planner
   musi ignorowac lub walidowac kontekst rozmowy
2. **Analysis Steps per-message** - analogicznie do poprawki insights (d7f872d)
3. **LIMIT preservation** - zweryfikowac ze sqlglot/validator nie usuwaja LIMIT
4. **Type safety w post-processingu** - try/except + pd.to_numeric() w chart_advisor
5. **Dashboard state cleanup** - czysc tytul/process/results po nowym zapytaniu
6. **Percentage SQL patterns** - dodac training examples z COUNT(CASE WHEN...)

### Istniejace priorytety (Q1-Q20 findings):

1. **Process Flow layout** - POPRAWIONY (LR dziala w Q26)
2. **Adaptacyjne rozmiary** komponentow
3. **Lepszy dobor typow wykresow** (pie heurystyka POPRAWIONA w Q25)
4. **Karty KPI** i **drill-down** sa kluczowe dla profesjonalnego BI

Implementacja poprawek Q21-Q30 powinna miec wyzszy priorytet niz nowe features,
poniewaz dotycza blednosci danych i halucynacji AI, co podwaza zaufanie uzytkownika.

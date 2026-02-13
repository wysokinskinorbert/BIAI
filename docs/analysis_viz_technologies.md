# Analiza technologii wizualizacji procesow biznesowych

**Projekt:** BIAI (Business Intelligence AI)
**Kontekst:** Reflex 0.8.x (Python -> React), dark mode, animacje, efekty glow
**Data:** 2026-02-13

---

## 1. Podsumowanie wykonawcze

Przeanalizowano 8 technologii pod katem wizualizacji animowanych procesow biznesowych
(BPMN-like) w aplikacji Reflex (Python -> React). Kluczowe kryteria: kompatybilnosc
z Reflex, mozliwosci animacji, dark mode, licencja open source, customizacja.

**REKOMENDACJA: React Flow (reactflow)** jako glowna technologia z opcjonalnym
uzyciem Mermaid.js dla prostych diagramow statycznych.

---

## 2. Szczegolowa analiza technologii

### 2.1 React Flow (reactflow / xyflow)

| Kryterium | Ocena | Komentarz |
|-----------|-------|-----------|
| Kompatybilnosc z Reflex | **5/5** | Oficjalny przyklad w dokumentacji Reflex. Reflex Enterprise ma dedykowany modul `rxe.react_flow`. Wrapping przez `rx.Component` / `rx.NoSSRComponent`. |
| Animacje procesow | **5/5** | AnimatedSVGEdge (animateMotion), Web Animations API, CSS keyframes. Animowane krawedzie, tokeny przesuwajace sie po sciezkach. |
| Wsparcie BPMN/process flow | **4/5** | Nie jest dedykowany BPMN, ale custom nodes pozwalaja odwzorowac dowolna notacje. Dagre/ELK layout dla automatycznego rozmieszczenia. |
| Dark mode | **5/5** | Natywny `colorMode="dark"` prop. CSS variables do pelnej customizacji. |
| Trudnosc integracji | **5/5** | Najlatwiejszy - Reflex ma gotowy wrapper. `pip install reflex-enterprise` lub wlasny wrap. Oficjalna dokumentacja z przykladami. |
| Licencja | **5/5** | MIT License. Darmowe uzywanie komercyjne. Brak ograniczen. |
| Spolecznosc/dokumentacja | **5/5** | 27k+ GitHub stars, aktywny rozwoj (v12.9.0, 2025-10). Doskonala dokumentacja z interaktywnymi przykladami. |
| Customizacja wygladu | **5/5** | Turbo Flow: glow effects, gradient borders, animowane krawedzie. Pelna kontrola CSS, custom nodes/edges jako React components. |
| **SREDNIA** | **4.9/5** | |

**Kluczowe zalety:**
- Jedyna technologia z oficjalnym wsparciem w Reflex (docs + Enterprise)
- Turbo Flow example: dokladnie ten styl wizualny (glow, dark, gradients) jakiego potrzebujemy
- Dagre integration dla automatycznego layout grafow skierowanych
- Custom nodes moga renderowac dowolny React component (ikony, progressbary, statusy)
- Interaktywnosc: drag & drop, zoom, pan, minimap, selection
- Event handlers: on_nodes_change, on_connect, on_edge_click etc.

**Przyklad integracji z Reflex (uproszczony):**
```python
import reflex as rx

class ReactFlowLib(rx.NoSSRComponent):
    library = "@xyflow/react@12.9.0"
    tag = "ReactFlow"

    nodes: rx.Var[list[dict]]
    edges: rx.Var[list[dict]]
    color_mode: rx.Var[str] = "dark"
    fit_view: rx.Var[bool] = True

    on_nodes_change: rx.EventHandler
    on_edges_change: rx.EventHandler
    on_connect: rx.EventHandler

    def _get_custom_code(self) -> str:
        return """import '@xyflow/react/dist/style.css';"""
```

**Wady:**
- Reflex Enterprise (z React Flow) wymaga platnej licencji Reflex
- Wlasny wrap wymaga wiedzy o React component lifecycle
- Brak natywnej notacji BPMN (trzeba budowac custom nodes)

---

### 2.2 Mermaid.js

| Kryterium | Ocena | Komentarz |
|-----------|-------|-----------|
| Kompatybilnosc z Reflex | **3/5** | Brak oficjalnego wrappera. Mozliwe przez `rx.html` z `<div class="mermaid">` lub `rx.script` z CDN. Alternatywnie mermaid-py (server-side rendering do SVG). |
| Animacje procesow | **2/5** | Ograniczone: animated edges (stroke-dasharray), ale brak token simulation, brak animacji przejsc miedzy stanami. Wymaga CSS hackow. |
| Wsparcie BPMN/process flow | **4/5** | Natywne flowcharts, sequence diagrams, state diagrams. Tekstowa definicja (DSL). 30+ nowych ksztaltow w 2025. |
| Dark mode | **4/5** | Wbudowany theme "dark". Customizacja przez `%%{init: {'theme':'dark'}}%%`. |
| Trudnosc integracji | **3/5** | Srednia - brak gotowego Reflex component, ale mermaid-py moze generowac SVG server-side. |
| Licencja | **5/5** | MIT License. |
| Spolecznosc/dokumentacja | **5/5** | 75k+ GitHub stars. Ogromna spolecznosc. Doskonala dokumentacja. |
| Customizacja wygladu | **2/5** | Ograniczona do themes i classDef. Brak pelnej kontroli CSS nad poszczegolnymi elementami. Brak glow/gradient effects. |
| **SREDNIA** | **3.5/5** | |

**Kluczowe zalety:**
- Najprostsza definicja diagramow (tekst DSL)
- Doskonale do statycznych/dokumentacyjnych diagramow
- Mozna generowac server-side (mermaid-py) i wysylac jako SVG/PNG

**Wady:**
- Brak interaktywnosci (nie mozna klikac, przeciagac nodow)
- Animacje ograniczone do CSS stroke-dasharray
- Brak custom event handlers
- Nie nadaje sie do dynamicznych, interaktywnych wizualizacji procesow

---

### 2.3 BPMN.js / react-bpmn

| Kryterium | Ocena | Komentarz |
|-----------|-------|-----------|
| Kompatybilnosc z Reflex | **2/5** | Brak wrappera Reflex. react-bpmn istnieje ale jest uproszczony (tylko display). Pelny bpmn-js wymaga zlozonego wrappowania. |
| Animacje procesow | **3/5** | bpmn-js-token-simulation plugin - animacja tokenow przechodzacych przez proces. Overlay API do highlightowania elementow. |
| Wsparcie BPMN/process flow | **5/5** | Najlepsza zgodnosc z BPMN 2.0. Natywny parser/renderer BPMN XML. Pelna specyfikacja. |
| Dark mode | **2/5** | Brak natywnego dark mode. Wymaga custom CSS override. |
| Trudnosc integracji | **2/5** | Wysoka - bpmn-js ma zlozony API, wymaga BPMN XML jako input. react-bpmn uproszczony. |
| Licencja | **4/5** | bpmn-io/bpmn-js: bpmn.io License (similarna do MIT, ale z ograniczeniami). |
| Spolecznosc/dokumentacja | **4/5** | Aktywny projekt bpmn.io (Camunda). Dobra dokumentacja. |
| Customizacja wygladu | **3/5** | Modyfikacja przez CSS i overlay API. Brak pelnej swobody jak w React Flow. |
| **SREDNIA** | **3.1/5** | |

**Kluczowe zalety:**
- Pelna zgodnosc z BPMN 2.0 standard
- Token simulation plugin (animacja procesu)
- Idealny jesli wymagana jest import/export BPMN XML

**Wady:**
- Wymaga BPMN XML jako input (nadmiarowa zlozonosc)
- Brak natywnego dark mode
- Trudna integracja z Reflex
- Overengineered jesli nie potrzebujemy pelnej specyfikacji BPMN

---

### 2.4 Apache ECharts

| Kryterium | Ocena | Komentarz |
|-----------|-------|-----------|
| Kompatybilnosc z Reflex | **3/5** | Brak oficjalnego wrappera. echarts-for-react (npm) mozna wrapowac. Alternatywnie pyecharts (Python) ale nie React. |
| Animacje procesow | **3/5** | Dobre animacje chart/graph. Sankey diagrams z animowanymi flow. Brak dedykowanego process flow. |
| Wsparcie BPMN/process flow | **2/5** | Graph layout, Sankey, Tree - ale nie process/workflow flow. Brak notacji BPMN. |
| Dark mode | **5/5** | Natywny dark theme. Pelna customizacja kolorow. |
| Trudnosc integracji | **3/5** | Srednia - wymaga wrappowania echarts-for-react. |
| Licencja | **5/5** | Apache 2.0 License. |
| Spolecznosc/dokumentacja | **5/5** | 62k+ GitHub stars. Apache Foundation projekt. Doskonala dokumentacja. |
| Customizacja wygladu | **4/5** | Bardzo duze mozliwosci customizacji chartow. GPU-accelerated rendering. |
| **SREDNIA** | **3.75/5** | |

**Kluczowe zalety:**
- Doskonale do chartow i wizualizacji danych (juz uzywany w BIAI przez Plotly)
- Sankey diagrams dla flow danych
- GPU-accelerated rendering

**Wady:**
- Nie jest biblioteką do workflow/process diagramow
- Brak drag & drop, interaktywnego edytowania grafow
- Lepszy do analityki niz do wizualizacji procesow

---

### 2.5 D3.js

| Kryterium | Ocena | Komentarz |
|-----------|-------|-----------|
| Kompatybilnosc z Reflex | **2/5** | Brak wrappera. D3 manipuluje DOM bezposrednio - konflikty z React virtual DOM. Wymaga ostrożnej integracji (useRef + useEffect). |
| Animacje procesow | **5/5** | Pelna kontrola nad SVG animacjami. Transitions, interpolations, force layouts. Mozliwe dowolne animacje. |
| Wsparcie BPMN/process flow | **3/5** | Brak dedykowanego - trzeba budowac od zera. Force-directed layouts, custom SVG rendering. |
| Dark mode | **4/5** | Pelna kontrola CSS/SVG - mozna zaimplementowac dowolny theme. |
| Trudnosc integracji | **1/5** | Bardzo wysoka - D3 + React to znany problem. D3 chce kontrolowac DOM, React tez. Wrappowanie w Reflex jeszcze trudniejsze. |
| Licencja | **5/5** | ISC License (permissive). |
| Spolecznosc/dokumentacja | **5/5** | 110k+ GitHub stars. Ogromna spolecznosc. |
| Customizacja wygladu | **5/5** | Pelna kontrola - SVG, Canvas, WebGL. Dowolny wyglad. |
| **SREDNIA** | **3.75/5** | |

**Kluczowe zalety:**
- Najwyzsza mozliwa kontrola nad wizualizacja
- Dowolne animacje SVG

**Wady:**
- Ogromny naklad pracy (budowanie od zera)
- Konflikt D3 DOM manipulation z React virtual DOM
- Bardzo trudna integracja z Reflex
- Overengineered dla naszego use case (React Flow robi to samo latwiej)

---

### 2.6 Cytoscape.js

| Kryterium | Ocena | Komentarz |
|-----------|-------|-----------|
| Kompatybilnosc z Reflex | **3/5** | react-cytoscapejs (npm) istnieje. Mozna wrapowac w Reflex. Plotly utrzymuje React wrapper. |
| Animacje procesow | **3/5** | ele.animation() API. Mozna animowac pozycje, style elementow. Brak dedykowanych process flow animations. |
| Wsparcie BPMN/process flow | **3/5** | Graph layouts (dagre, cola, klay). Nie dedykowany process flow ale mozna odwzorowac. |
| Dark mode | **3/5** | Stylesheet-based styling. Mozna implementowac dark mode przez runtime stylesheet swap. |
| Trudnosc integracji | **3/5** | Srednia - react-cytoscapejs wrapper. Ostatnia aktualizacja wrappera: 3 lata temu. |
| Licencja | **5/5** | MIT License. |
| Spolecznosc/dokumentacja | **4/5** | 10k+ GitHub stars. Dobra dokumentacja. Bardziej akademicki/naukowy charakter. |
| Customizacja wygladu | **3/5** | CSS-like stylesheets. Mniej elastyczny niz React Flow custom nodes. |
| **SREDNIA** | **3.4/5** | |

**Kluczowe zalety:**
- Dobry do wizualizacji grafow/sieci
- Algorithm-heavy (analiza grafow, shortest path, clustering)

**Wady:**
- React wrapper nieaktualizowany (3 lata)
- Bardziej naukowy niz biznesowy charakter
- Mniej elastyczny niz React Flow dla custom UI

---

### 2.7 GoJS

| Kryterium | Ocena | Komentarz |
|-----------|-------|-----------|
| Kompatybilnosc z Reflex | **3/5** | gojs-react component istnieje. Mozna wrapowac. |
| Animacje procesow | **4/5** | Animation API, custom animations. Dobre wsparcie flow diagramow. |
| Wsparcie BPMN/process flow | **5/5** | Dedykowane BPMN templates, swimlanes, process flows. |
| Dark mode | **4/5** | Theme system z dark mode. |
| Trudnosc integracji | **3/5** | Srednia - gojs-react wrapper dostepny. |
| Licencja | **1/5** | **KOMERCYJNA - $3,995/licencja.** Nie open source. Watermark w darmowej wersji. |
| Spolecznosc/dokumentacja | **4/5** | Doskonala dokumentacja. Profesjonalne wsparcie (platne). |
| Customizacja wygladu | **4/5** | Duze mozliwosci. Templates, shapes, styles. |
| **SREDNIA** | **3.5/5** | |

**WYKLUCZONE** - Licencja komercyjna ($3,995). Nie spelnia wymogu open source.

---

### 2.8 Dagre

| Kryterium | Ocena | Komentarz |
|-----------|-------|-----------|
| Kompatybilnosc z Reflex | **2/5** | Dagre to algorytm layout, nie biblioteka UI. Uzywa sie go Z innymi bibliotekami (np. React Flow). |
| Animacje procesow | **1/5** | Brak - to tylko algorytm rozmieszczenia nodow. |
| Wsparcie BPMN/process flow | **3/5** | Directed graph layout - dobre do rozmieszczenia procesow. |
| Dark mode | **N/A** | Nie dotyczy - brak UI. |
| Trudnosc integracji | **4/5** | Latwa integracja z React Flow (oficjalny przyklad). |
| Licencja | **5/5** | MIT License. |
| Spolecznosc/dokumentacja | **3/5** | Stabilny ale nieaktywny (legacy). |
| Customizacja wygladu | **N/A** | Nie dotyczy - brak UI. |
| **SREDNIA** | **N/A** | Komplementarny do React Flow |

**Dagre to layout engine, nie samodzielna biblioteka wizualizacji.**
Uzywa sie go jako plugin do React Flow lub Cytoscape.js dla automatycznego
rozmieszczenia nodow w grafach skierowanych.

---

## 3. Macierz porownawcza

| Technologia | Reflex | Animacje | BPMN | Dark | Integracja | Licencja | Community | Custom | SUMA |
|-------------|--------|----------|------|------|------------|----------|-----------|--------|------|
| **React Flow** | 5 | 5 | 4 | 5 | 5 | 5 (MIT) | 5 | 5 | **39** |
| ECharts | 3 | 3 | 2 | 5 | 3 | 5 (Apache) | 5 | 4 | 30 |
| D3.js | 2 | 5 | 3 | 4 | 1 | 5 (ISC) | 5 | 5 | 30 |
| Mermaid.js | 3 | 2 | 4 | 4 | 3 | 5 (MIT) | 5 | 2 | 28 |
| GoJS | 3 | 4 | 5 | 4 | 3 | **1** | 4 | 4 | 28* |
| Cytoscape.js | 3 | 3 | 3 | 3 | 3 | 5 (MIT) | 4 | 3 | 27 |
| BPMN.js | 2 | 3 | 5 | 2 | 2 | 4 | 4 | 3 | 25 |

*GoJS wykluczone z powodu licencji komercyjnej*

---

## 4. REKOMENDACJA

### Glowna technologia: React Flow (reactflow / @xyflow/react)

**Uzasadnienie:**

1. **Najlepsza integracja z Reflex** - jedyna technologia z oficjalnym przykladem w dokumentacji Reflex i dedykowanym modulem w Reflex Enterprise.

2. **Turbo Flow = nasz docelowy styl** - gotowy przyklad z glow effects, gradient borders, animated edges, dark theme. Dokladnie to czego potrzebujemy.

3. **Dagre layout** - automatyczne rozmieszczenie nodow w grafach skierowanych (idealne dla procesow biznesowych z krokami sekwencyjnymi i rownoleglymi).

4. **Custom nodes** - kazdy node to React component, mozna renderowac: ikony BPMN, status procesu, progress bar, metryki, kolorowe oznaczenia.

5. **Animowane krawedzie** - AnimatedSVGEdge z tokenami przesuwajacymi sie po krawedziach, idealne do wizualizacji przeplywu procesu.

6. **Interaktywnosc** - zoom, pan, drag & drop, selection, minimap - pelna interakcja uzytkownika.

7. **MIT License** - darmowe do uzytku komercyjnego.

8. **Aktywny rozwoj** - v12.9.0 (2025-10), 27k+ stars, doskonala dokumentacja.

### Opcjonalnie: Mermaid.js jako uzupelnienie

Mermaid.js moze byc uzywany do:
- Statycznych diagramow w dokumentacji/raportach
- Szybkiego prototypowania procesow (tekstowa definicja DSL)
- Server-side rendering diagramow (mermaid-py -> SVG/PNG)

Ale **NIE** jako glowna technologia wizualizacji interaktywnej.

### Proponowana architektura

```
+----------------------------------+
|          Reflex Frontend         |
|  +----------------------------+  |
|  |  Custom React Flow Wrapper |  |
|  |  (rx.NoSSRComponent)       |  |
|  |                            |  |
|  |  +-- Custom Process Nodes  |  |
|  |  |   (BPMN-like shapes)    |  |
|  |  |   - Start/End events    |  |
|  |  |   - Tasks/Activities    |  |
|  |  |   - Gateways (XOR/AND)  |  |
|  |  |   - Subprocesses        |  |
|  |  +-- Custom Animated Edges |  |
|  |  |   - Token flow animation|  |
|  |  |   - Gradient colors     |  |
|  |  |   - Glow effects        |  |
|  |  +-- Dagre Auto-Layout     |  |
|  |  +-- Dark Theme + Glow CSS |  |
|  +----------------------------+  |
|                                  |
|  ProcessVisualizationState       |
|  - nodes: list[dict]            |
|  - edges: list[dict]            |
|  - process_status: dict         |
|  - animation_config: dict       |
+----------------------------------+
           |
           v
+----------------------------------+
|       Reflex Backend (Python)    |
|  - Process definition loader     |
|  - Real-time status updates      |
|  - Oracle DB process data        |
+----------------------------------+
```

### Szacowany naklad integracji

| Etap | Opis | Zlozonosc |
|------|------|-----------|
| 1. React Flow Wrapper | Wrap @xyflow/react w Reflex component | Srednia (1-2 dni) |
| 2. Custom Process Nodes | 5-6 typow nodow BPMN-like | Srednia (2-3 dni) |
| 3. Animated Edges | SVG animation + glow CSS | Niska (1 dzien) |
| 4. Dagre Layout | Auto-layout procesow | Niska (0.5 dnia) |
| 5. Dark Theme + Glow | CSS variables, gradients | Niska (0.5 dnia) |
| 6. State Management | ProcessVisualizationState | Srednia (1-2 dni) |
| 7. Backend Integration | Ladowanie procesow z Oracle | Srednia (1-2 dni) |

**Laczny szacowany naklad: 7-11 dni roboczych**

### Alternatywne podejscie: Reflex Enterprise

Jesli projekt ma licencje Reflex Enterprise:
- `pip install reflex-enterprise`
- Gotowy `rxe.react_flow` modul
- Mniejszy naklad pracy (2-3 dni mniej)
- Ale: wymaga platnej licencji Reflex

---

## 5. Zrodla

- [React Flow - oficjalna dokumentacja](https://reactflow.dev/)
- [React Flow - Dark Mode](https://reactflow.dev/examples/styling/dark-mode)
- [React Flow - Animated Edges](https://reactflow.dev/examples/edges/animating-edges)
- [React Flow - Turbo Flow (glow effects)](https://reactflow.dev/examples/styling/turbo-flow)
- [React Flow - Dagre Layout](https://reactflow.dev/examples/layout/dagre)
- [React Flow - Custom Nodes](https://reactflow.dev/examples/nodes/custom-node)
- [Reflex - Wrapping React Example (ReactFlow)](https://reflex.dev/docs/wrapping-react/example/)
- [Reflex Enterprise - React Flow Components](https://reflex.dev/docs/enterprise/react-flow/components/)
- [Mermaid.js - Flowchart Syntax](https://mermaid.js.org/syntax/flowchart.html)
- [Mermaid.js - Theming](https://mermaid.js.org/config/theming.html)
- [bpmn.js - BPMN 2.0 Toolkit](https://bpmn.io/toolkit/bpmn-js/)
- [bpmn-visualization-js](https://github.com/process-analytics/bpmn-visualization-js)
- [Apache ECharts](https://echarts.apache.org/)
- [Cytoscape.js](https://js.cytoscape.org/)
- [react-cytoscapejs](https://github.com/plotly/react-cytoscapejs)
- [Dagre - Directed Graph Layout](https://github.com/dagrejs/dagre)
- [xyflow MIT License Discussion](https://github.com/xyflow/xyflow/discussions/3397)
- [GoJS Pricing](https://nwoods.com/sales)

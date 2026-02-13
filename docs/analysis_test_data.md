# BIAI - Dane testowe procesow biznesowych

## Przeglad

Skrypt `scripts/oracle-process-seed.sql` tworzy 4 zestawy tabel procesow biznesowych
w bazie Oracle XE (XEPDB1). Dane sa powiazane z istniejacymi tabelami z `oracle-seed.sql`
(customers, employees, orders, products, sales_regions).

## Tabele procesow

### 1. Order Fulfillment Process

| Tabela | Opis | Wierszy |
|--------|------|---------|
| `ORDER_PROCESS_LOG` | Log przejsc stanow zamowien | ~500-700 |

**Stany:** `order_placed` -> `payment_pending` -> `payment_confirmed` -> `warehouse_assigned` -> `picking` -> `packing` -> `shipped` -> `in_transit` -> `delivered`

**Kolumny:**
- `process_id` (PK, IDENTITY)
- `order_id` (FK -> orders)
- `from_status`, `to_status` - przejscie stanu
- `changed_by` (FK -> employees)
- `changed_at` (TIMESTAMP)
- `notes` - opis przejscia
- `duration_minutes` - czas trwania etapu

**Wbudowane wzorce:**
- Bottleneck na etapie `packing` (60-480 min vs 5-90 min dla innych)
- `in_transit` najdluzszy (720-4320 min = 0.5-3 dni)
- ~85% zamowien dochodzi do `delivered`
- Powiazanie z istniejacymi zamowieniami (orders.status = delivered/shipped/confirmed)

**View:** `V_ORDER_PROCESS_BOTTLENECKS` - sredni czas trwania kazdego etapu

---

### 2. Sales Pipeline (CRM)

| Tabela | Opis | Wierszy |
|--------|------|---------|
| `SALES_PIPELINE` | Aktualne szanse sprzedazowe | ~300 |
| `PIPELINE_HISTORY` | Historia przejsc etapow | ~800-1200 |

**Stany:** `lead` -> `qualified` -> `proposal` -> `negotiation` -> `closed_won` / `closed_lost`

**Kolumny (sales_pipeline):**
- `pipeline_id` (PK, IDENTITY)
- `customer_id` (FK -> customers)
- `employee_id` (FK -> employees, sales 1-10)
- `stage` - aktualny etap
- `entered_at` (TIMESTAMP)
- `expected_value` - oczekiwana wartosc deala
- `probability` - prawdopodobienstwo (0-100%)
- `product_interest` - produkt zainteresowania
- `deal_source` - zrodlo leada (Website/Referral/Trade Show/Cold Call/Partner/Inbound Marketing)

**Wbudowane wzorce:**
- ~30% closed_won, ~20% closed_lost, reszta w roznych etapach aktywnych
- Utracone deale: 40% na etapie qualified, 35% na proposal, 25% na negotiation
- Wartosci dealow: 5,000 - 200,000
- Rozne zrodla leadow z roznym rozkladem

**View:** `V_PIPELINE_FUNNEL` - lejek konwersji po etapach

---

### 3. Support Ticket Workflow

| Tabela | Opis | Wierszy |
|--------|------|---------|
| `SUPPORT_TICKETS` | Zgloszenia wsparcia | ~250 |
| `TICKET_HISTORY` | Historia zmian statusu | ~800-1200 |

**Stany:** `new` -> `assigned` -> `investigating` -> `waiting_customer` -> `in_progress` -> `resolved` -> `closed` / `reopened`

**Kolumny (support_tickets):**
- `ticket_id` (PK, IDENTITY)
- `customer_id` (FK -> customers)
- `assigned_to` (FK -> employees, support 21-24)
- `priority` - P1/P2/P3/P4
- `category` - Login Issue/Performance/Data Error/Integration/Billing/Feature Request/Bug Report/Configuration/Access Control/Documentation
- `subject` - temat zgloszenia
- `status` - aktualny status
- `created_at`, `updated_at`, `resolved_at`
- `resolution_minutes` - czas do rozwiazania

**Wbudowane wzorce:**
- SLA zalezy od priorytetu: P1 (30min-4h), P2 (2h-1d), P3 (8h-3d), P4 (1-7d)
- 60% zamknietych, 15% resolved, reszta w roznych stanach aktywnych
- 40% ticketow przechodzi przez `waiting_customer`
- ~3% ticketow jest `reopened`
- 4 inzynierowie support z roznym obciazeniem

**Views:**
- `V_TICKET_SLA_ANALYSIS` - analiza SLA per priorytet
- `V_SUPPORT_WORKLOAD` - obciazenie per inzynier support

---

### 4. Approval Workflow

| Tabela | Opis | Wierszy |
|--------|------|---------|
| `APPROVAL_REQUESTS` | Wnioski o zatwierdzenie | ~200 |
| `APPROVAL_STEPS` | Kroki zatwierdzania | ~600-900 |

**Stany:** `draft` -> `submitted` -> `level1_review` -> `level2_review` -> `approved` / `rejected` -> `executed`

**Kolumny (approval_requests):**
- `request_id` (PK, IDENTITY)
- `requester_id` (FK -> employees)
- `request_type` - purchase/travel/hiring/budget/expense
- `description` - opis wniosku
- `amount` - kwota
- `current_step` - aktualny krok
- `status` - active/completed/rejected/cancelled

**Wbudowane wzorce:**
- Kwoty wyzsze >20,000: wymagaja level2, wyzszy wskaznik odrzucen (~20%)
- Kwoty nizsze <5,000: tylko level1, niski wskaznik odrzucen (~8%)
- Kwoty srednie: level2, umiarkowane odrzucenia (~12%)
- Typy: purchase (500-50k), travel (200-8k), hiring (50k-180k), budget (10k-500k), expense (50-5k)

**View:** `V_APPROVAL_EFFICIENCY` - efektywnosc procesow zatwierdzania

---

## Przykladowe pytania do AI

### Order Fulfillment

1. "Ktory etap realizacji zamowien trwa najdluzej?"
2. "Pokaz sredni czas trwania kazdego etapu procesu zamowien"
3. "Ile zamowien utkneło na etapie packing?"
4. "Jaki jest sredni czas od zlozenia zamowienia do dostawy?"
5. "Ktory pracownik przetwarza najwiecej zamowien?"
6. "Pokaz rozklad czasow in_transit w dniach"

### Sales Pipeline

7. "Jaki jest wskaznik konwersji w lejku sprzedazy?"
8. "Ile jest aktywnych dealow w fazie negotiation?"
9. "Jaka jest laczna wartosc dealow closed_won?"
10. "Ktory handlowiec ma najlepsza konwersje?"
11. "Z jakiego zrodla pochodzi najwiecej closed_won?"
12. "Pokaz sredni czas przejscia miedzy etapami pipeline"
13. "Jaki procent dealow jest tracony na kazdym etapie?"
14. "Pokaz lejek sprzedazy z wartosciami na kazdym etapie"

### Support Tickets

15. "Jaki jest sredni czas rozwiazania ticketow P1 vs P4?"
16. "Ile ticketow jest aktualnie otwartych?"
17. "Ktora kategoria zgloszenia ma najdluzszy czas rozwiazania?"
18. "Pokaz rozklad ticketow po priorytetach i statusach"
19. "Ktory inzynier support ma najwyzsze obciazenie?"
20. "Ile procent ticketow jest ponownie otwieranych (reopened)?"
21. "Jaki jest trend liczby nowych ticketow miesiecznie?"

### Approval Workflow

22. "Ile procent wnioskow jest odrzucanych?"
23. "Jaki jest sredni czas zatwierdzania wnioskow?"
24. "Ktory typ wniosku ma najwyzszy wskaznik odrzucen?"
25. "Pokaz rozklad kwot wnioskow po typach"
26. "Ile wnioskow czeka na level2_review?"
27. "Kto skladal najwyzsze wnioski budzetowe?"

### Cross-process (pytania laczace procesy)

28. "Pokaz korelacje miedzy wartoscia zamowienia a czasem realizacji"
29. "Czy klienci z wiekszymi zamowieniami zglaszaja wiecej ticketow?"
30. "Pokaz timeline aktywnosci - zamowienia, tickety, wnioski - miesiecznie"

## Schemat relacji

```
orders (istniejaca)
  |
  +---> order_process_log (FK: order_id)
  |        |
  |        +---> employees (FK: changed_by)
  |
customers (istniejaca)
  |
  +---> sales_pipeline (FK: customer_id)
  |        |
  |        +---> employees (FK: employee_id)
  |        +---> pipeline_history (FK: pipeline_id)
  |
  +---> support_tickets (FK: customer_id)
           |
           +---> employees (FK: assigned_to)
           +---> ticket_history (FK: ticket_id)

employees (istniejaca)
  |
  +---> approval_requests (FK: requester_id)
           |
           +---> approval_steps (FK: request_id)
                    |
                    +---> employees (FK: approver_id)
```

## Uruchamianie

```bash
# Wymagania: Oracle XE w Docker na porcie 1521
# Najpierw uruchom oracle-seed.sql (jesli jeszcze nie uruchomiony)
sqlplus biai/biai123@//localhost:1521/XEPDB1 @scripts/oracle-seed.sql

# Nastepnie uruchom skrypt procesow
sqlplus biai/biai123@//localhost:1521/XEPDB1 @scripts/oracle-process-seed.sql
```

## Views analityczne

| View | Opis |
|------|------|
| `V_ORDER_PROCESS_BOTTLENECKS` | Bottlenecki w procesie zamowien (avg/median/max czas per etap) |
| `V_PIPELINE_FUNNEL` | Lejek konwersji sprzedazy (count/value per etap) |
| `V_TICKET_SLA_ANALYSIS` | Analiza SLA ticketow (avg resolution per priority+status) |
| `V_APPROVAL_EFFICIENCY` | Efektywnosc zatwierdzania (count/amount per type+step+status) |
| `V_SUPPORT_WORKLOAD` | Obciazenie inzynierow support (open/resolved/avg time) |

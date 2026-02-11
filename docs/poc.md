PROJEKT: Local AI Business Analyst (MVP)

Typ dokumentu: Specyfikacja Techniczna i Prompt dla AI Developera Data: 2026-02-11
1. Cel Projektu

Stworzenie lekkiej, nowoczesnej aplikacji w Pythonie typu "Business Intelligence Chatbot". Aplikacja ma umożliwiać użytkownikom nietechnicznym zadawanie pytań w języku naturalnym do lokalnej bazy danych Oracle i otrzymywanie odpowiedzi w formie:

    Wykresów interaktywnych (Plotly/ECharts).

    Diagramów procesowych/przepływów (Mermaid.js/Graphviz).

    Tabel z danymi.

Kluczowym założeniem jest prywatność i lokalność (użycie lokalnych modeli LLM przez Ollama) oraz brak kosztów licencyjnych (tylko open source).
2. Stack Technologiczny (Wymagany)

Jako Senior Python Developer, masz użyć następujących technologii:

    Język: Python 3.10+

    UI/UX (Frontend): Streamlit (najnowsza wersja).

        Layout: st.set_page_config(layout="wide") - układ dwukolumnowy (Lewa: Czat, Prawa: Prezentacja wyników).

    Wizualizacja:

        streamlit-echarts (do animowanych, nowoczesnych wykresów i przepływów).

        plotly (do standardowych wykresów biznesowych).

        streamlit.components.v1 + Mermaid.js (do diagramów ERD i sekwencji).

    Baza Danych: python-oracledb (w trybie Thin Mode – aby nie wymagać instalacji Oracle Instant Client).

    AI/LLM Backend:

        ollama (biblioteka python) – do komunikacji z lokalnym modelem (np. qwen2.5-coder lub llama3).

        Prompt Engineering: Bezpośrednie prompty systemowe (bez ciężkich frameworków jak LangChain na tym etapie, aby uniknąć over-engineeringu).

    Przetwarzanie danych: pandas.

3. Architektura i Wzorce Projektowe
A. Modularność (Konektory)

Aplikacja musi być przygotowana na rozszerzenie o PostgreSQL/MongoDB w przyszłości.

    Stwórz abstrakcyjną klasę/interfejs DatabaseConnector.

    Zaimplementuj klasę OracleConnector dziedziczącą po interfejsie.

    Metody interfejsu: connect(), get_schema_summary() (zwraca DDL/listę tabel), execute_query(sql_query).

B. Przepływ Danych (Agent Workflow)

    User Input: Użytkownik wpisuje pytanie w oknie czatu.

    Schema Retrieval: Aplikacja pobiera uproszczony schemat bazy (tylko nazwy tabel i kluczowych kolumn) – Context.

    Reasoning (LLM):

        Prompt do LLM zawiera: Schema + Pytanie Użytkownika.

        LLM decyduje: "Czy potrzebuję SQL?" czy "Czy to prośba o diagram struktury?".

    Action:

        Jeśli dane liczbowe: LLM generuje SQL -> Python wykonuje SQL -> Pandas DataFrame.

        Jeśli diagram procesu: LLM generuje kod Mermaid/Graphviz na podstawie logów/dat w bazie.

    Visualization (LLM):

        LLM otrzymuje próbkę danych (DataFrame.head()) i decyduje o typie wizualizacji (JSON dla ECharts lub Config dla Plotly).

    Render: UI wyświetla wynik w oknie prezentacji.

4. Wymagania Funkcjonalne (MVP)
Interfejs Użytkownika (UI)

    Sidebar:

        Konfiguracja połączenia do Oracle (Host, Port, Service Name, User, Password).

        Przycisk "Połącz i Pobierz Schemat".

        Wybór modelu Ollama z listy dostępnych lokalnie.

    Obszar Główny (Split Screen):

        Kolumna Lewa (Chat): Historia rozmowy, pole input. Stylizacja dymków (User vs AI).

        Kolumna Prawa (Canvas/Dashboard): Tu pojawiają się wygenerowane artefakty:

            Karta z wykresem (z opcją powiększenia).

            Diagramy Mermaid renderowane jako HTML.

            Tabele danych.

Logika Biznesowa

    Text-to-SQL: Model musi generować poprawny składniowo SQL dla Oracle (uwaga na cudzysłowy i dialekt Oracle).

    Ochrona: Konektor wykonuje tylko zapytania SELECT (tryb Read-Only wymuszony w kodzie lub via użytkownika DB).

    Samonaprawa: Jeśli SQL zwróci błąd (np. "ORA-00904: invalid identifier"), aplikacja powinna wysłać błąd z powrotem do LLM z prośbą o poprawkę zapytania.

5. Instrukcja dla AI Developera (Twoje Zadanie)

Jako AI Developer, wygeneruj kompletny kod źródłowy w pliku app.py oraz plik pomocniczy db_utils.py.

    Setup środowiska: Załóż, że użytkownik ma postawionego Oracle XE w Dockerze (gvenzl/oracle-xe) dostępnego na localhost:1521.

    Styl: Kod ma być czysty, z komentarzami (Type Hinting), zgodny z PEP8.

    Obsługa Błędów: Dodaj bloki try-except przy połączeniu z bazą i wykonywaniu zapytań generated przez AI.

    Mock Data (Opcjonalnie): Jeśli nie uda się połączyć z bazą, dodaj "Tryb Demo", który używa zahardkodowanego DataFrame, aby pokazać możliwości UI.

Kluczowe dla UI: Zadbaj o to, aby wykresy ECharts wyglądały nowocześnie (Dark Mode, animacje, efekt "glow").
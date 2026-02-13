"""30 AI question tests on real Docker PostgreSQL + Ollama.

Tests the full pipeline: question → Vanna SQL generation → validation →
execution on real database. Zero mocks.

Requires:
    1. docker compose -f docker-compose.dev.yml up -d postgres-test
    2. Ollama running locally (http://localhost:11434) with model loaded

Run:
    pytest tests/test_ai_questions.py -v --timeout=120

Each test verifies:
    - Pipeline returns success (SQL generated and executed)
    - Result has minimum expected rows
    - Generated SQL references expected tables
"""

import pytest

from biai.ai.pipeline import AIPipeline
from biai.models.connection import ConnectionConfig, DBType
from biai.db.postgresql import PostgreSQLConnector
from biai.config.constants import DEFAULT_MODEL, DEFAULT_OLLAMA_HOST

pytestmark = pytest.mark.ai_questions


# ---------------------------------------------------------------------------
# Session-scoped fixtures (real DB + AI pipeline)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
async def pg_connector():
    """Real PostgreSQL connector for AI tests."""
    config = ConnectionConfig(
        db_type=DBType.POSTGRESQL,
        host="localhost",
        port=5433,
        database="biai_test",
        username="biai",
        password="biai123",
    )
    connector = PostgreSQLConnector(config)
    await connector.connect()
    yield connector
    await connector.disconnect()


@pytest.fixture(scope="session")
async def ai_pipeline(pg_connector):
    """Real AIPipeline with Vanna + Ollama + PostgreSQL.

    Trains schema once per session (expensive but necessary).
    """
    pipeline = AIPipeline(
        connector=pg_connector,
        db_type=DBType.POSTGRESQL,
        ollama_model=DEFAULT_MODEL,
        ollama_host=DEFAULT_OLLAMA_HOST,
    )
    await pipeline.train_schema()
    return pipeline


# ---------------------------------------------------------------------------
# Parametrized AI question tests (30 questions)
# ---------------------------------------------------------------------------

# Format: (question, expected_tables, min_rows)
# expected_tables: at least one must appear in the generated SQL
# min_rows: minimum number of rows expected in the result

ORDER_FULFILLMENT = [
    (
        "Ktory etap realizacji zamowien trwa najdluzej?",
        ["order_process_log"],
        1,
    ),
    (
        "Pokaz sredni czas trwania kazdego etapu procesu zamowien",
        ["order_process_log"],
        3,
    ),
    (
        "Ile zamowien utknelo na etapie packing?",
        ["order_process_log"],
        1,
    ),
    (
        "Jaki jest sredni czas od zlozenia zamowienia do dostawy?",
        ["order_process_log", "orders"],
        1,
    ),
    (
        "Ktory pracownik przetwarza najwiecej zamowien?",
        ["order_process_log", "employees"],
        1,
    ),
    (
        "Pokaz rozklad czasow in_transit w dniach",
        ["order_process_log"],
        1,
    ),
]

SALES_PIPELINE = [
    (
        "Jaki jest wskaznik konwersji w lejku sprzedazy?",
        ["sales_pipeline"],
        1,
    ),
    (
        "Ile jest aktywnych dealow w fazie negotiation?",
        ["sales_pipeline"],
        1,
    ),
    (
        "Jaka jest laczna wartosc dealow closed_won?",
        ["sales_pipeline"],
        1,
    ),
    (
        "Ktory handlowiec ma najlepsza konwersje?",
        ["sales_pipeline", "employees"],
        1,
    ),
    (
        "Z jakiego zrodla pochodzi najwiecej closed_won?",
        ["sales_pipeline"],
        1,
    ),
    (
        "Pokaz sredni czas przejscia miedzy etapami pipeline",
        ["pipeline_history"],
        1,
    ),
    (
        "Jaki procent dealow jest tracony na kazdym etapie?",
        ["sales_pipeline"],
        1,
    ),
    (
        "Pokaz lejek sprzedazy z wartosciami na kazdym etapie",
        ["sales_pipeline"],
        1,
    ),
]

SUPPORT_TICKETS = [
    (
        "Jaki jest sredni czas rozwiazania ticketow P1 vs P4?",
        ["support_tickets"],
        1,
    ),
    (
        "Ile ticketow jest aktualnie otwartych?",
        ["support_tickets"],
        1,
    ),
    (
        "Ktora kategoria zgloszenia ma najdluzszy czas rozwiazania?",
        ["support_tickets"],
        1,
    ),
    (
        "Pokaz rozklad ticketow po priorytetach i statusach",
        ["support_tickets"],
        1,
    ),
    (
        "Ktory inzynier support ma najwyzsze obciazenie?",
        ["support_tickets", "employees"],
        1,
    ),
    (
        "Ile procent ticketow jest ponownie otwieranych?",
        ["support_tickets", "ticket_history"],
        1,
    ),
    (
        "Jaki jest trend liczby nowych ticketow miesiecznie?",
        ["support_tickets"],
        1,
    ),
]

APPROVAL_WORKFLOW = [
    (
        "Ile procent wnioskow jest odrzucanych?",
        ["approval_requests"],
        1,
    ),
    (
        "Jaki jest sredni czas zatwierdzania wnioskow?",
        ["approval_requests", "approval_steps"],
        1,
    ),
    (
        "Ktory typ wniosku ma najwyzszy wskaznik odrzucen?",
        ["approval_requests"],
        1,
    ),
    (
        "Pokaz rozklad kwot wnioskow po typach",
        ["approval_requests"],
        1,
    ),
    (
        "Ile wnioskow czeka na level2_review?",
        ["approval_requests"],
        1,
    ),
    (
        "Kto skladal najwyzsze wnioski budzetowe?",
        ["approval_requests", "employees"],
        1,
    ),
]

CROSS_PROCESS = [
    (
        "Pokaz korelacje miedzy wartoscia zamowienia a czasem realizacji",
        ["orders", "order_process_log"],
        1,
    ),
    (
        "Czy klienci z wiekszymi zamowieniami zglaszaja wiecej ticketow?",
        ["customers", "orders", "support_tickets"],
        1,
    ),
    (
        "Pokaz timeline aktywnosci zamowienia tickety wnioski miesiecznie",
        ["orders", "support_tickets", "approval_requests"],
        1,
    ),
]

ALL_QUESTIONS = (
    ORDER_FULFILLMENT
    + SALES_PIPELINE
    + SUPPORT_TICKETS
    + APPROVAL_WORKFLOW
    + CROSS_PROCESS
)


@pytest.mark.parametrize(
    "question,expected_tables,min_rows",
    ALL_QUESTIONS,
    ids=[f"Q{i+1}" for i in range(len(ALL_QUESTIONS))],
)
async def test_ai_question(ai_pipeline, question, expected_tables, min_rows):
    """Test a single AI question against real database."""
    result = await ai_pipeline.process(question)

    # 1. Pipeline succeeded
    assert result.success, (
        f"Pipeline failed for: {question}\n"
        f"Errors: {result.errors}\n"
        f"Query error: {result.query_error}"
    )

    # 2. Got results
    assert result.query_result is not None, f"No query result for: {question}"
    assert result.query_result.row_count >= min_rows, (
        f"Expected >= {min_rows} rows, got {result.query_result.row_count}\n"
        f"SQL: {result.sql_query.sql}"
    )

    # 3. SQL references at least one expected table
    sql_lower = result.sql_query.sql.lower()
    found = any(table in sql_lower for table in expected_tables)
    assert found, (
        f"None of expected tables {expected_tables} found in SQL:\n{result.sql_query.sql}"
    )

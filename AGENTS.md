# Repository Guidelines

## Project Structure & Module Organization
Core application code lives in `biai/`:
- `biai/ai/` for NL-to-SQL pipeline, process discovery, chart logic, and LLM integrations.
- `biai/db/` for Oracle/PostgreSQL connectors and schema management.
- `biai/state/` for Reflex state classes used by UI workflows.
- `biai/components/` for UI components (charts, React Flow, dashboard, chat).
- `biai/models/` for Pydantic domain models.

Tests are in `tests/` (main suite) and `biai/tests/` (module-focused tests).  
Docs and architecture notes are under `docs/`.  
Seed SQL and local test DB fixtures are in `scripts/`.

## Build, Test, and Development Commands
- `python -m venv .venv && .venv\Scripts\activate` - create and activate virtual env (Windows).
- `pip install -e ".[dev]"` - install app + test dependencies from `pyproject.toml`.
- `reflex run` - start the app locally.
- `.\start.ps1 -Dev` - convenience startup (checks Ollama, optional Docker, then Reflex).
- `pytest` - run full test suite.
- `pytest -m integration` - run Docker-backed integration tests.
- `docker compose -f docker-compose.dev.yml up -d` - start Oracle XE + PostgreSQL test databases.

## Coding Style & Naming Conventions
Use Python with PEP 8 conventions, 4-space indentation, and explicit type hints.  
Prefer `snake_case` for functions/modules, `PascalCase` for classes, and short, descriptive names aligned with existing files (e.g., `process_discovery.py`, `SchemaState`).  
Keep async boundaries explicit (`async def`, `await`) in DB/state/AI flows.  
Follow existing Pydantic-first modeling style for structured data.

## Testing Guidelines
Framework: `pytest` with `pytest-asyncio`.  
Test files follow `test_*.py`; test classes use `Test*`; test names should describe behavior (`test_detect_transition_columns`).  
Add unit tests for each logic change and integration tests for connector/pipeline behavior when schema/query behavior changes.

## Commit & Pull Request Guidelines
Use Conventional Commit style seen in history: `feat:`, `fix:`, `docs:`, `chore:`.  
Keep commits focused and scoped (one functional change per commit).  
PRs should include:
- concise problem/solution summary,
- affected modules (e.g., `biai/ai/process_discovery.py`),
- test evidence (`pytest`, markers used),
- UI screenshots/GIFs for component changes.

## Security & Configuration Tips
Never commit secrets. Use `.env` (loaded via `pydantic-settings`) for local configuration.  
Use read-only DB users where possible.  
Treat generated SQL as read-only; do not weaken validator safeguards in `biai/ai/sql_validator.py`.

## Agent-Specific UI Test Routing
When user intent is browser/UI testing, use the global skill `ui-web-testing` and run MCP browser tools automatically.

Trigger phrases (case-insensitive, including close variants/typos):
- `testu UI`
- `przetestuj w przeglądarce`
- `test w UI`
- `test UI`
- `UI test`
- `browser test`

Execution policy:
- Default tool: `playwright` MCP for deterministic end-to-end flows.
- Use `chrome-devtools` MCP for deep diagnosis (DOM/CSS, console, network, performance) or visual-debug confirmation.
- Prefer hybrid loop for hard bugs: reproduce in Playwright, inspect in DevTools, verify in Playwright.
- Optimize token usage with snapshot-first evidence, minimal screenshots, and compact pass/fail reporting.

# BIAI - Architecture Document

## Overview

BIAI (Business Intelligence AI) is a local AI-powered business analyst chatbot
that allows non-technical users to query Oracle and PostgreSQL databases
using natural language, receiving answers as interactive charts, tables, and insights.

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Reflex (Python → React) |
| Charts | ECharts + Plotly |
| AI/LLM | Ollama + Qwen2.5-Coder-7B |
| Text-to-SQL | Vanna.ai (RAG) |
| Vector DB | ChromaDB |
| SQL Parser | sqlglot |
| Oracle | python-oracledb (thin) |
| PostgreSQL | asyncpg |
| Config | pydantic-settings |
| Deploy | Docker Compose |

## Architecture Layers

```
UI Layer (Reflex Components)
    ↓
State Layer (Reflex State)
    ↓
AI Layer (Vanna + Pipeline)
    ↓
Data Layer (DB Connectors)
    ↓
Infrastructure (Docker)
```

## Data Flow

1. User asks question → ChatState
2. RAG retrieval → ChromaDB
3. SQL generation → Vanna + Qwen2.5-Coder
4. SQL validation → sqlglot AST
5. Self-correction → max 3 retries
6. Execute query → DataFrame
7. Chart selection → ECharts/Plotly
8. Render → Dashboard + Stream description

## Security (4 layers)

1. sqlglot AST → only SELECT
2. Regex patterns → block dangerous keywords
3. Single statement → block injection via ;
4. DB user should be read-only

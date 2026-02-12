"""Prompt templates for LLM interactions."""


SYSTEM_PROMPT = """You are an expert SQL analyst. Your job is to generate precise, read-only SQL queries
based on user questions and the database schema provided.

RULES:
1. Generate ONLY SELECT statements. Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or any DDL/DML.
2. Always use table and column names exactly as they appear in the schema.
3. Use appropriate aggregate functions (COUNT, SUM, AVG, MIN, MAX) when the question implies aggregation.
4. Add ORDER BY for ranking/top-N queries.
5. Use aliases for calculated columns to make results readable.
6. Keep queries efficient - avoid SELECT * when specific columns are needed.
7. Follow the dialect rules provided below.

{dialect_rules}
"""

CORRECTION_PROMPT = """The previous SQL query failed with the following error:

**SQL:**
```sql
{sql}
```

**Error:**
{error}

Please fix the SQL query. Remember:
- Only generate a SELECT statement
- Follow the {dialect} dialect rules
- Make sure all table and column names match the schema exactly
- Return ONLY the corrected SQL, nothing else
"""

CHART_ADVISOR_PROMPT = """Given the following SQL query results, recommend the best chart type and configuration.

**Question:** {question}
**SQL:** {sql}
**Columns:** {columns}
**Sample data (first 5 rows):**
{sample_data}
**Row count:** {row_count}

Respond in this exact JSON format:
{{
    "chart_type": "bar|line|pie|scatter|area|table",
    "x_column": "column_name_for_x_axis",
    "y_columns": ["column_name_for_y_axis"],
    "title": "Chart title",
    "reasoning": "Brief explanation"
}}

Guidelines:
- Use "pie" for proportions/percentages (max 10 categories)
- Use "bar" for comparing categories
- Use "line" for time series data
- Use "scatter" for correlations between two numeric columns
- Use "area" for cumulative time series
- Use "table" if data doesn't suit visualization
"""

DESCRIPTION_PROMPT = """Based on the query results, provide a brief, insightful description for a business user.

**Question:** {question}
**SQL executed:** {sql}
**Result summary:** {row_count} rows returned. Columns: {columns}
**Key data points:**
{key_points}

Write 2-3 sentences highlighting the key findings. Be specific with numbers. Use business-friendly language.
Do not use LaTeX, mathematical notation, or dollar signs for formatting. Use plain text only.
"""


def format_dialect_rules(rules: list[str]) -> str:
    """Format dialect rules into the system prompt."""
    if not rules:
        return ""
    rules_text = "\n".join(f"- {rule}" for rule in rules)
    return f"DIALECT-SPECIFIC RULES:\n{rules_text}"

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
8. For count/distribution queries per status, stage, type, or category column, ALWAYS use GROUP BY.
   Example: "how many X per status" → SELECT status, COUNT(*) AS cnt FROM table GROUP BY status ORDER BY cnt DESC.
   NEVER use CASE WHEN to manually enumerate status values when GROUP BY achieves the same result.

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
    "chart_type": "bar|line|pie|scatter|area|treemap|sunburst|radar|parallel|table",
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
- Use "treemap" for hierarchical data (parent-child, 2+ category columns)
- Use "sunburst" for nested categories with values
- Use "radar" for multi-dimensional comparison (few rows, 3+ numeric columns)
- Use "parallel" for high-dimensional numeric data (4+ numeric columns)
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
IMPORTANT: Only reference values and names that appear in the actual data above. Do NOT invent, estimate, or hallucinate any values.
CRITICAL: Do NOT generate any SQL code. Do NOT include ```sql blocks. Do NOT reason about queries. Only write a plain text business summary.
"""


PROCESS_DISCOVERY_PROMPT = """Analyze this database schema and the discovered process candidates below.
For each candidate, provide a business-friendly interpretation.

**Database schema (tables and columns):**
{schema_ddl}

**Discovered candidates:**
{candidates_json}

Respond in this exact JSON format (a list):
[
  {{
    "id": "candidate_id_from_input",
    "name": "Human-Friendly Process Name",
    "description": "2-3 sentence business description of this process",
    "stages": ["stage1", "stage2", "stage3"],
    "branches": {{"gateway_stage": ["branch1", "branch2"]}},
    "stage_labels": {{"stage_id": "Human Label"}},
    "stage_colors": {{"stage_id": "#hexcolor"}},
    "stage_icons": {{"stage_id": "lucide-icon-name"}}
  }}
]

Guidelines:
- Order stages in the logical business sequence (start to end)
- Branches are alternative paths from a gateway stage
- Use short, clear labels for stages
- Use hex colors that convey meaning (green=success, red=failure, blue=active, yellow=waiting)
- Use Lucide icon names (e.g., "truck", "check-circle", "clock", "user")
- If you cannot determine the process, set confidence to 0 and return minimal data
"""

PROCESS_DESCRIPTION_PROMPT = """Describe this business process based on the data below.

**Process name:** {process_name}
**Tables involved:** {tables}
**Stages found:** {stages}
**Stage counts:** {stage_counts}

Provide a 3-4 sentence business-friendly description of what this process does,
who uses it, and what the key stages mean. Use plain text only, no markdown.
"""


CONTEXT_PROMPT = """The user is having a multi-turn conversation. Here is the context from previous exchanges:

{context}

The current question may reference previous results. Use the context to understand references like
"the same", "that data", "those results", "compare with", "also show", "now filter by", etc.
"""

INSIGHT_PROMPT = """Analyze the following query results and provide 2-3 key business insights.

**Question:** {question}
**SQL:** {sql}
**Columns:** {columns}
**Row count:** {row_count}
**Statistics:**
{statistics}

For each insight, respond in this exact JSON format:
[
  {{
    "type": "anomaly|trend|correlation|pareto|distribution",
    "title": "Short insight title (5-10 words)",
    "description": "1-2 sentence explanation with specific numbers",
    "severity": "info|warning|critical"
  }}
]

Guidelines:
- Focus on ACTIONABLE insights, not just data summaries
- Use specific numbers (percentages, counts, values)
- Pareto: check if 80% of results come from 20% of categories
- Anomaly: flag values > 2 standard deviations from mean
- Trend: note if data increases/decreases consistently
- Keep it concise and business-friendly
"""

ANALYSIS_PLAN_PROMPT = """Break down this complex question into simple SQL query steps.

**Question:** {question}
**Available tables and columns:**
{schema_summary}
**Conversation context:**
{context}

Respond in this exact JSON format:
{{
  "is_complex": true/false,
  "steps": [
    {{
      "step": 1,
      "type": "sql",
      "description": "What this step does",
      "depends_on": [],
      "question_for_sql": "Simple question that can be answered with one SQL query"
    }}
  ],
  "final_combination": "How to combine the results of all steps"
}}

If the question can be answered with a single SQL query, set is_complex to false and return one step.
Only decompose into multiple steps if the question truly requires comparing separate query results.
"""

STORYTELLING_PROMPT = """Create a data narrative from these analysis results.

**Question:** {question}
**Key findings:**
{findings}
**Insights:**
{insights}

Write a structured narrative with:
1. **Context** — What was analyzed and why it matters (1 sentence)
2. **Key Findings** — The most important discoveries with specific numbers (2-3 bullet points)
3. **Implications** — What this means for the business (1-2 sentences)
4. **Recommendations** — What action to take next (1-2 bullet points)

Use business-friendly language. Be specific with numbers. No LaTeX or special formatting.
"""


def format_dialect_rules(rules: list[str]) -> str:
    """Format dialect rules into the system prompt."""
    if not rules:
        return ""
    rules_text = "\n".join(f"- {rule}" for rule in rules)
    return f"DIALECT-SPECIFIC RULES:\n{rules_text}"

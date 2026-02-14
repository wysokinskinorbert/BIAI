"""SQL dialect helpers for Oracle vs PostgreSQL."""

from __future__ import annotations

from biai.models.connection import DBType
from biai.models.schema import SchemaSnapshot


class DialectHelper:
    """Provides dialect-specific SQL rules and examples."""

    ORACLE_RULES = [
        "Use FETCH FIRST N ROWS ONLY instead of LIMIT (Oracle 12c+).",
        "Use NVL() instead of COALESCE() for simple null checks.",
        "Use SYSDATE for current date, not NOW().",
        "Use TO_DATE('2024-01-01', 'YYYY-MM-DD') for date literals.",
        "Use TO_CHAR() for date formatting.",
        "Use (+) or ANSI JOIN syntax for outer joins.",
        "String comparison is case-sensitive by default.",
        "Use DUAL table for SELECT without FROM: SELECT 1 FROM DUAL.",
        "Use ROWNUM or ROW_NUMBER() OVER() for row numbering.",
        "Use || for string concatenation.",
        "NEVER use bind variable syntax (:param_name). Use literal values directly in WHERE clauses.",
        # P2: Oracle INTERVAL→NUMBER conversion
        "To calculate minutes between two TIMESTAMPs, use: "
        "EXTRACT(DAY FROM (ts2 - ts1)) * 1440 + EXTRACT(HOUR FROM (ts2 - ts1)) * 60 + EXTRACT(MINUTE FROM (ts2 - ts1)). "
        "Do NOT use DATEDIFF or direct subtraction to get a NUMBER from TIMESTAMPs.",
        # P4: NVL for aggregations
        "When aggregating nullable columns, wrap with NVL(column, 0) to avoid NULL propagation: "
        "e.g. SUM(NVL(amount, 0)), AVG(NVL(duration_minutes, 0)).",
        "Use TO_CHAR(timestamp_col, 'YYYY-MM') to group by month in temporal/trend queries.",
    ]

    POSTGRESQL_RULES = [
        "Use LIMIT N OFFSET M for pagination.",
        "Use COALESCE() for null handling.",
        "Use NOW() or CURRENT_TIMESTAMP for current date/time.",
        "Use ::type for casting: '2024-01-01'::date.",
        "Use ILIKE for case-insensitive pattern matching.",
        "Use || for string concatenation.",
        "Use EXTRACT(field FROM date) for date parts.",
        "Use ARRAY_AGG() and STRING_AGG() for aggregation.",
        "Use DISTINCT ON (column) for distinct per group.",
        "Use GENERATE_SERIES() for sequence generation.",
    ]

    @classmethod
    def get_rules(cls, db_type: DBType) -> list[str]:
        if db_type == DBType.ORACLE:
            return cls.ORACLE_RULES
        return cls.POSTGRESQL_RULES

    @classmethod
    def get_examples(cls, db_type: DBType, schema: SchemaSnapshot | None = None) -> list[tuple[str, str]]:
        """Generate example queries from actual schema columns."""
        if not schema or not schema.tables:
            return []
        return _generate_examples_from_schema(schema, db_type)

    @classmethod
    def get_documentation(cls, schema: SchemaSnapshot) -> list[str]:
        """Generate natural-language documentation from schema."""
        if not schema or not schema.tables:
            return []
        return _generate_docs_from_schema(schema)

    @classmethod
    def get_dialect_name(cls, db_type: DBType) -> str:
        if db_type == DBType.ORACLE:
            return "oracle"
        return "postgres"

    @classmethod
    def get_sqlglot_dialect(cls, db_type: DBType) -> str:
        """Get sqlglot dialect string."""
        if db_type == DBType.ORACLE:
            return "oracle"
        return "postgres"


def _generate_docs_from_schema(schema: SchemaSnapshot) -> list[str]:
    """Generate natural-language documentation strings from schema snapshot."""
    docs = []

    # Determine schema prefix for table references
    schema_prefix = ""
    if schema.schema_name and schema.schema_name not in ("", "public", "USER"):
        schema_prefix = f"{schema.schema_name}."
        docs.append(
            f"IMPORTANT: All tables belong to schema {schema.schema_name}. "
            f"You MUST always use the schema prefix in queries: "
            f"{schema.schema_name}.TABLE_NAME (e.g., {schema.schema_name}.{schema.tables[0].name if schema.tables else 'TABLE'})."
        )

    # Overview doc — use full_name when schema prefix is present
    table_refs = [f"{schema_prefix}{t.name}" for t in schema.tables]
    docs.append(
        f"The database contains {len(table_refs)} tables: {', '.join(table_refs)}."
    )

    # Per-table documentation
    for table in schema.tables:
        col_descriptions = []
        pk_cols = []
        fk_descriptions = []
        tbl_ref = f"{schema_prefix}{table.name}"

        for col in table.columns:
            desc = f"{col.name} ({col.data_type})"
            if col.is_primary_key:
                pk_cols.append(col.name)
            if col.is_foreign_key and col.foreign_key_ref:
                fk_descriptions.append(
                    f"{col.name} references {col.foreign_key_ref}"
                )
            col_descriptions.append(desc)

        parts = [f"Table {tbl_ref} has columns: {', '.join(col_descriptions)}."]
        if pk_cols:
            parts.append(f"Primary key: {', '.join(pk_cols)}.")
        if fk_descriptions:
            parts.append(f"Foreign keys: {'; '.join(fk_descriptions)}.")

        docs.append(" ".join(parts))

    # Relationship summary
    relationships = []
    for table in schema.tables:
        tbl_ref = f"{schema_prefix}{table.name}"
        for col in table.columns:
            if col.is_foreign_key and col.foreign_key_ref:
                relationships.append(
                    f"{tbl_ref}.{col.name} -> {col.foreign_key_ref}"
                )
    if relationships:
        docs.append(
            f"Table relationships: {'; '.join(relationships)}."
        )

    # Column disambiguation — prevent AI from using wrong column names across tables
    docs.extend(_generate_column_disambiguation(schema))

    return docs


def _generate_column_disambiguation(schema: SchemaSnapshot) -> list[str]:
    """Generate explicit disambiguation docs for commonly confused columns.

    The AI often hallucinates column names by mixing columns from different tables.
    This documents which columns belong to which tables and warns about common mistakes.
    """
    docs: list[str] = []

    # Build a map: column_name -> list of tables that have it
    col_to_tables: dict[str, list[str]] = {}
    table_col_map: dict[str, set[str]] = {}
    for table in schema.tables:
        col_names = {col.name.upper() for col in table.columns}
        table_col_map[table.name.upper()] = col_names
        for col in table.columns:
            key = col.name.upper()
            col_to_tables.setdefault(key, []).append(table.name)

    # 1. Disambiguate status/stage-like columns (most common confusion)
    status_keywords = {"STATUS", "STAGE", "STEP", "PHASE", "STATE", "CURRENT_STEP"}
    transition_keywords = {"FROM_STATUS", "TO_STATUS", "FROM_STAGE", "TO_STAGE", "FROM_STEP", "TO_STEP"}

    status_cols_per_table: list[str] = []
    for table in schema.tables:
        table_status = []
        table_transition = []
        for col in table.columns:
            cu = col.name.upper()
            if cu in status_keywords:
                table_status.append(col.name)
            elif cu in transition_keywords:
                table_transition.append(col.name)

        if table_status or table_transition:
            all_cols = table_status + table_transition
            status_cols_per_table.append(
                f"{table.name} uses: {', '.join(all_cols)}"
            )

    if status_cols_per_table:
        docs.append(
            "IMPORTANT — Status/stage column mapping (DO NOT confuse between tables): "
            + "; ".join(status_cols_per_table)
            + ". Always use the exact column name for the table you are querying."
        )

    # 2. Warn about columns that exist in one table but NOT another
    confusable_pairs = [
        ("STAGE", "ORDER_PROCESS_LOG", "FROM_STATUS, TO_STATUS"),
        ("STATUS", "SALES_PIPELINE", "STAGE"),
        ("ENTERED_AT", "PIPELINE_HISTORY", "CHANGED_AT"),
        ("ACTED_AT", "APPROVAL_REQUESTS", "CREATED_AT, UPDATED_AT, COMPLETED_AT"),
    ]
    for wrong_col, table_name, correct_cols in confusable_pairs:
        tname_upper = table_name.upper()
        if tname_upper in table_col_map:
            if wrong_col.upper() not in table_col_map[tname_upper]:
                docs.append(
                    f"WARNING: {table_name} does NOT have a column named '{wrong_col}'. "
                    f"Use {correct_cols} instead."
                )

    # 3. Document date/timestamp columns per table for temporal queries
    date_keywords = {"DATE", "TIMESTAMP", "TIME", "CREATED", "UPDATED", "CHANGED"}
    date_docs: list[str] = []
    for table in schema.tables:
        date_cols = [
            col.name for col in table.columns
            if any(kw in col.name.upper() or kw in col.data_type.upper()
                   for kw in date_keywords)
        ]
        if date_cols:
            date_docs.append(f"{table.name}: {', '.join(date_cols)}")

    if date_docs:
        docs.append(
            "Date/timestamp columns per table: " + "; ".join(date_docs) + "."
        )

    return docs


def _generate_examples_from_schema(
    schema: SchemaSnapshot,
    db_type: DBType,
) -> list[tuple[str, str]]:
    """Generate example query pairs using REAL column names from schema."""
    examples: list[tuple[str, str]] = []
    is_oracle = db_type == DBType.ORACLE
    limit_clause = "FETCH FIRST {n} ROWS ONLY" if is_oracle else "LIMIT {n}"

    # Schema prefix for non-default schemas
    sp = ""
    if schema.schema_name and schema.schema_name not in ("", "public", "USER"):
        sp = f"{schema.schema_name}."

    table_map = {t.name.upper(): t for t in schema.tables}

    # Example 1: Simple SELECT with LIMIT from first table
    if schema.tables:
        t = schema.tables[0]
        col_names = ", ".join(c.name for c in t.columns[:4])
        examples.append((
            f"Show first 10 rows from {t.name}",
            f"SELECT {col_names} FROM {sp}{t.name} ORDER BY {t.columns[0].name} {limit_clause.format(n=10)}",
        ))

    # Example 2: COUNT per table
    for t in schema.tables[:2]:
        examples.append((
            f"How many rows in {t.name}?",
            f"SELECT COUNT(*) AS row_count FROM {sp}{t.name}",
        ))

    # Example 3: JOIN query using FK relationships
    for t in schema.tables:
        for col in t.columns:
            if col.is_foreign_key and col.foreign_key_ref:
                ref_name = col.foreign_key_ref.upper()
                ref_table = table_map.get(ref_name)
                if ref_table:
                    # Find PK of referenced table
                    ref_pk = next((c.name for c in ref_table.columns if c.is_primary_key), ref_table.columns[0].name)
                    # Pick a display column from referenced table (not PK)
                    ref_display = next(
                        (c.name for c in ref_table.columns if not c.is_primary_key),
                        ref_table.columns[0].name,
                    )
                    examples.append((
                        f"Show {t.name} with {ref_table.name} details",
                        f"SELECT a.*, b.{ref_display} FROM {sp}{t.name} a "
                        f"JOIN {sp}{ref_table.name} b ON a.{col.name} = b.{ref_pk} "
                        f"{limit_clause.format(n=20)}",
                    ))

    # Example 4: Aggregation if numeric columns exist (skip PK/FK for aggregation)
    for t in schema.tables:
        numeric_cols = [
            c for c in t.columns
            if _is_numeric_type(c.data_type) and not c.is_primary_key and not c.is_foreign_key
        ]
        group_cols = [c for c in t.columns if not _is_numeric_type(c.data_type) and not c.is_primary_key]
        if numeric_cols and group_cols:
            num_col = numeric_cols[0].name
            grp_col = group_cols[0].name
            examples.append((
                f"Show total {num_col} grouped by {grp_col} from {t.name}",
                f"SELECT {grp_col}, SUM({num_col}) AS total_{num_col.lower()} "
                f"FROM {sp}{t.name} GROUP BY {grp_col} "
                f"ORDER BY total_{num_col.lower()} DESC {limit_clause.format(n=10)}",
            ))
            break  # One aggregation example is enough

    # P7: Cross-process UNION ALL examples for timeline/trend queries
    examples.extend(_generate_cross_process_examples(schema, db_type))

    return examples


def _generate_cross_process_examples(
    schema: SchemaSnapshot, db_type: DBType,
) -> list[tuple[str, str]]:
    """Generate cross-table UNION ALL examples for timeline/monthly trend queries."""
    examples: list[tuple[str, str]] = []
    is_oracle = db_type == DBType.ORACLE

    # Schema prefix for non-default schemas
    sp = ""
    if schema.schema_name and schema.schema_name not in ("", "public", "USER"):
        sp = f"{schema.schema_name}."

    # Find tables with date/timestamp columns for timeline queries
    table_dates: list[tuple[str, str]] = []  # (table_name, date_col_name)
    for table in schema.tables:
        for col in table.columns:
            dtype_upper = col.data_type.upper()
            col_upper = col.name.upper()
            if ("DATE" in dtype_upper or "TIMESTAMP" in dtype_upper) and \
               col_upper in {"CREATED_AT", "ORDER_DATE", "CHANGED_AT", "UPDATED_AT"}:
                table_dates.append((table.name, col.name))
                break  # one date col per table

    if len(table_dates) >= 2:
        # Build a UNION ALL monthly count example
        parts = []
        for tname, dcol in table_dates[:3]:
            parts.append(
                f"SELECT TO_CHAR({dcol}, 'YYYY-MM') AS month, "
                f"'{tname}' AS source, COUNT(*) AS cnt "
                f"FROM {sp}{tname} GROUP BY TO_CHAR({dcol}, 'YYYY-MM')"
            )
        union_sql = " UNION ALL ".join(parts) + " ORDER BY month"
        table_names = ", ".join(t for t, _ in table_dates[:3])
        examples.append((
            f"Show monthly activity timeline across {table_names}",
            union_sql,
        ))

    return examples


def _is_numeric_type(data_type: str) -> bool:
    """Check if a column data type is numeric."""
    dt = data_type.upper()
    return any(kw in dt for kw in ("NUMBER", "INT", "DECIMAL", "NUMERIC", "FLOAT", "DOUBLE", "REAL", "MONEY"))


# ---------------------------------------------------------------------------
# P3: Auto-discover DISTINCT values for status/stage/type columns
# ---------------------------------------------------------------------------

# Column names that likely hold categorical status values worth documenting
_CATEGORICAL_COLUMN_KEYWORDS = {
    "STATUS", "STAGE", "STEP", "PHASE", "STATE", "TYPE", "ACTION",
    "CURRENT_STEP", "FROM_STATUS", "TO_STATUS", "FROM_STAGE", "TO_STAGE",
    "CATEGORY", "PRIORITY", "DEAL_SOURCE", "REQUEST_TYPE", "SEGMENT",
    "DEPARTMENT",
}


def get_categorical_columns(schema: SchemaSnapshot) -> list[tuple[str, str]]:
    """Return (table_name, column_name) pairs for categorical columns worth discovering.

    Only includes VARCHAR/CHAR columns whose name matches known categorical keywords.
    """
    results: list[tuple[str, str]] = []
    for table in schema.tables:
        for col in table.columns:
            if col.is_primary_key or col.is_foreign_key:
                continue
            # Check column name against keywords
            col_upper = col.name.upper()
            dtype_upper = col.data_type.upper()
            is_string = any(kw in dtype_upper for kw in ("VARCHAR", "CHAR", "TEXT", "NVARCHAR"))
            if is_string and col_upper in _CATEGORICAL_COLUMN_KEYWORDS:
                results.append((table.full_name, col.name))
    return results


def build_distinct_values_docs(distinct_map: dict[str, dict[str, list[str]]]) -> list[str]:
    """Convert a {table: {column: [values]}} map into training documentation strings.

    Args:
        distinct_map: {table_name: {col_name: [val1, val2, ...]}}

    Returns:
        List of documentation strings for Vanna training.
    """
    docs: list[str] = []
    for table, cols in distinct_map.items():
        for col, values in cols.items():
            if not values:
                continue
            vals_str = ", ".join(f"'{v}'" for v in values)
            docs.append(
                f"IMPORTANT: The column {table}.{col} contains these exact values (case-sensitive): "
                f"{vals_str}. Always use these exact values in WHERE clauses."
            )
    return docs

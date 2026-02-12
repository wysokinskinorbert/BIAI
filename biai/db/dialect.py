"""SQL dialect helpers for Oracle vs PostgreSQL."""

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

    # Overview doc
    table_names = [t.name for t in schema.tables]
    docs.append(
        f"The database contains {len(table_names)} tables: {', '.join(table_names)}."
    )

    # Per-table documentation
    for table in schema.tables:
        col_descriptions = []
        pk_cols = []
        fk_descriptions = []

        for col in table.columns:
            desc = f"{col.name} ({col.data_type})"
            if col.is_primary_key:
                pk_cols.append(col.name)
            if col.is_foreign_key and col.foreign_key_ref:
                fk_descriptions.append(
                    f"{col.name} references {col.foreign_key_ref}"
                )
            col_descriptions.append(desc)

        parts = [f"Table {table.name} has columns: {', '.join(col_descriptions)}."]
        if pk_cols:
            parts.append(f"Primary key: {', '.join(pk_cols)}.")
        if fk_descriptions:
            parts.append(f"Foreign keys: {'; '.join(fk_descriptions)}.")

        docs.append(" ".join(parts))

    # Relationship summary
    relationships = []
    for table in schema.tables:
        for col in table.columns:
            if col.is_foreign_key and col.foreign_key_ref:
                relationships.append(
                    f"{table.name}.{col.name} -> {col.foreign_key_ref}"
                )
    if relationships:
        docs.append(
            f"Table relationships: {'; '.join(relationships)}."
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

    table_map = {t.name.upper(): t for t in schema.tables}

    # Example 1: Simple SELECT with LIMIT from first table
    if schema.tables:
        t = schema.tables[0]
        col_names = ", ".join(c.name for c in t.columns[:4])
        examples.append((
            f"Show first 10 rows from {t.name}",
            f"SELECT {col_names} FROM {t.name} ORDER BY {t.columns[0].name} {limit_clause.format(n=10)}",
        ))

    # Example 2: COUNT per table
    for t in schema.tables[:2]:
        examples.append((
            f"How many rows in {t.name}?",
            f"SELECT COUNT(*) AS row_count FROM {t.name}",
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
                        f"SELECT a.*, b.{ref_display} FROM {t.name} a "
                        f"JOIN {ref_table.name} b ON a.{col.name} = b.{ref_pk} "
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
                f"FROM {t.name} GROUP BY {grp_col} "
                f"ORDER BY total_{num_col.lower()} DESC {limit_clause.format(n=10)}",
            ))
            break  # One aggregation example is enough

    return examples


def _is_numeric_type(data_type: str) -> bool:
    """Check if a column data type is numeric."""
    dt = data_type.upper()
    return any(kw in dt for kw in ("NUMBER", "INT", "DECIMAL", "NUMERIC", "FLOAT", "DOUBLE", "REAL", "MONEY"))

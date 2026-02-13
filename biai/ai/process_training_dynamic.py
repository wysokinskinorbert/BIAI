"""Dynamic process training data generator.

Generates Vanna documentation and SQL examples from DiscoveredProcess objects
instead of hardcoded process_training.py data.
"""

from biai.models.discovery import DiscoveredProcess
from biai.models.schema import SchemaSnapshot
from biai.utils.logger import get_logger

logger = get_logger(__name__)


class DynamicProcessTrainer:
    """Generates training docs and examples from discovered processes."""

    def generate_documentation(
        self,
        processes: list[DiscoveredProcess],
        schema: SchemaSnapshot,
    ) -> list[str]:
        """Generate domain documentation strings for Vanna training."""
        docs: list[str] = []

        for proc in processes:
            # Basic process description
            tables_str = ", ".join(proc.tables)
            stages_str = " -> ".join(proc.stages) if proc.stages else "unknown stages"
            desc = proc.description or f"Business process in {tables_str}."

            docs.append(
                f"{proc.name}: {desc} "
                f"Tables involved: {tables_str}. "
                f"Process stages in order: {stages_str}."
            )

            # Transition pattern documentation
            if proc.transition_pattern:
                tp = proc.transition_pattern
                docs.append(
                    f"Table {tp.table_name} records state transitions for {proc.name}. "
                    f"Column {tp.from_column} is the source state and {tp.to_column} is the target state. "
                    f"Use GROUP BY {tp.from_column}, {tp.to_column} to analyze transition patterns."
                )
                if tp.timestamp_column:
                    docs.append(
                        f"Column {tp.timestamp_column} in {tp.table_name} records when each transition occurred."
                    )

            # Status column documentation
            if proc.status_column:
                sc = proc.status_column
                if sc.distinct_values:
                    vals = ", ".join(sc.distinct_values[:20])
                    docs.append(
                        f"Column {sc.column_name} in table {sc.table_name} tracks the {proc.name} status. "
                        f"Known values: {vals}."
                    )

            # Stage counts
            if proc.stage_counts:
                counts_str = ", ".join(
                    f"{k}: {v}" for k, v in sorted(
                        proc.stage_counts.items(), key=lambda x: -x[1]
                    )[:10]
                )
                docs.append(
                    f"Current distribution for {proc.name}: {counts_str}."
                )

            # Branches
            if proc.branches:
                for gateway, targets in proc.branches.items():
                    label = proc.get_label(gateway)
                    target_labels = [proc.get_label(t) for t in targets]
                    docs.append(
                        f"In {proc.name}, from '{label}' the process can branch to: "
                        f"{', '.join(target_labels)}."
                    )

        if docs:
            logger.info("dynamic_training_docs_generated", count=len(docs))
        return docs

    def generate_examples(
        self,
        processes: list[DiscoveredProcess],
        is_oracle: bool = False,
    ) -> list[tuple[str, str]]:
        """Generate example (question, SQL) pairs for Vanna training."""
        examples: list[tuple[str, str]] = []
        limit = "FETCH FIRST {n} ROWS ONLY" if is_oracle else "LIMIT {n}"

        for proc in processes:
            if proc.transition_pattern:
                examples.extend(self._transition_examples(proc, limit))
            elif proc.status_column:
                examples.extend(self._status_examples(proc, limit))

        if examples:
            logger.info("dynamic_training_examples_generated", count=len(examples))
        return examples

    def _transition_examples(
        self,
        proc: DiscoveredProcess,
        limit_tpl: str,
    ) -> list[tuple[str, str]]:
        """Generate examples for transition-based processes."""
        tp = proc.transition_pattern
        if not tp:
            return []
        table = tp.table_name
        fr = tp.from_column
        to = tp.to_column
        name = proc.name

        examples = [
            (
                f"Show transition counts for {name}",
                f"SELECT {fr}, {to}, COUNT(*) AS transition_count "
                f"FROM {table} "
                f"WHERE {fr} IS NOT NULL AND {to} IS NOT NULL "
                f"GROUP BY {fr}, {to} "
                f"ORDER BY transition_count DESC",
            ),
            (
                f"How many items are at each stage in {name}?",
                f"SELECT {to} AS stage, COUNT(*) AS stage_count "
                f"FROM {table} "
                f"GROUP BY {to} "
                f"ORDER BY stage_count DESC",
            ),
        ]

        if tp.timestamp_column:
            examples.append((
                f"Show recent transitions in {name}",
                f"SELECT {fr}, {to}, {tp.timestamp_column} "
                f"FROM {table} "
                f"ORDER BY {tp.timestamp_column} DESC "
                + limit_tpl.format(n=20),
            ))

        return examples

    def _status_examples(
        self,
        proc: DiscoveredProcess,
        limit_tpl: str,
    ) -> list[tuple[str, str]]:
        """Generate examples for status-column-based processes."""
        sc = proc.status_column
        if not sc:
            return []
        table = sc.table_name
        col = sc.column_name
        name = proc.name

        return [
            (
                f"Show distribution of {name} statuses",
                f"SELECT {col}, COUNT(*) AS status_count "
                f"FROM {table} "
                f"GROUP BY {col} "
                f"ORDER BY status_count DESC",
            ),
            (
                f"How many records are in each {name} stage?",
                f"SELECT {col} AS stage, COUNT(*) AS total "
                f"FROM {table} "
                f"WHERE {col} IS NOT NULL "
                f"GROUP BY {col} "
                f"ORDER BY total DESC",
            ),
        ]

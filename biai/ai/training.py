"""Schema trainer for Vanna.ai RAG."""

from biai.models.schema import SchemaSnapshot
from biai.utils.logger import get_logger

logger = get_logger(__name__)


class SchemaTrainer:
    """Trains Vanna with DDL, documentation, and example queries."""

    def __init__(self, vanna_client):
        self._vanna = vanna_client

    def train_ddl(self, schema: SchemaSnapshot) -> int:
        """Train Vanna with DDL statements from schema."""
        count = 0
        for table in schema.tables:
            ddl = table.get_ddl()
            try:
                self._vanna.train(ddl=ddl)
                count += 1
                logger.debug("trained_ddl", table=table.name)
            except Exception as e:
                logger.warning("train_ddl_failed", table=table.name, error=str(e))
        logger.info("ddl_training_complete", tables_trained=count)
        return count

    def train_documentation(self, docs: list[str]) -> int:
        """Train with business documentation / semantic layer."""
        count = 0
        for doc in docs:
            try:
                self._vanna.train(documentation=doc)
                count += 1
            except Exception as e:
                logger.warning("train_doc_failed", error=str(e))
        logger.info("doc_training_complete", docs_trained=count)
        return count

    def train_examples(self, examples: list[tuple[str, str]]) -> int:
        """Train with question-SQL example pairs."""
        count = 0
        for question, sql in examples:
            try:
                self._vanna.train(question=question, sql=sql)
                count += 1
            except Exception as e:
                logger.warning("train_example_failed", question=question[:50], error=str(e))
        logger.info("example_training_complete", examples_trained=count)
        return count

    def train_full(
        self,
        schema: SchemaSnapshot,
        docs: list[str] | None = None,
        examples: list[tuple[str, str]] | None = None,
    ) -> dict[str, int]:
        """Full training pipeline."""
        results = {
            "ddl": self.train_ddl(schema),
            "docs": self.train_documentation(docs or []),
            "examples": self.train_examples(examples or []),
        }
        logger.info("full_training_complete", **results)
        return results

    def get_training_data(self) -> list[dict]:
        """Get current training data from Vanna."""
        try:
            return self._vanna.get_training_data().to_dict("records")
        except Exception:
            return []

    def remove_training_data(self, training_id: str) -> bool:
        """Remove a specific training data entry."""
        try:
            self._vanna.remove_training_data(id=training_id)
            return True
        except Exception as e:
            logger.warning("remove_training_failed", id=training_id, error=str(e))
            return False

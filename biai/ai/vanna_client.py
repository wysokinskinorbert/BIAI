"""Vanna.ai client with ChromaDB + Ollama integration."""

from vanna.chromadb import ChromaDB_VectorStore
from vanna.ollama import Ollama

from biai.config.constants import DEFAULT_MODEL, DEFAULT_OLLAMA_HOST, DEFAULT_CHROMA_COLLECTION
from biai.utils.logger import get_logger

logger = get_logger(__name__)


class MyVanna(ChromaDB_VectorStore, Ollama):
    """Custom Vanna class combining ChromaDB vector store with Ollama LLM."""

    def __init__(self, config: dict | None = None):
        if config is None:
            config = {}
        ChromaDB_VectorStore.__init__(self, config=config)
        Ollama.__init__(self, config=config)
        logger.info(
            "vanna_initialized",
            model=config.get("model", "unknown"),
            ollama_host=config.get("ollama_host", "unknown"),
        )

    def reset_collections(self):
        """Delete and recreate all ChromaDB collections (fixes corrupted HNSW indices)."""
        for name in ["documentation", "ddl", "sql"]:
            try:
                self.chroma_client.delete_collection(name)
                logger.info("chromadb_collection_deleted", collection=name)
            except Exception:
                pass
        self.documentation_collection = self.chroma_client.get_or_create_collection(
            name="documentation",
            embedding_function=self.embedding_function,
        )
        self.ddl_collection = self.chroma_client.get_or_create_collection(
            name="ddl",
            embedding_function=self.embedding_function,
        )
        self.sql_collection = self.chroma_client.get_or_create_collection(
            name="sql",
            embedding_function=self.embedding_function,
        )
        logger.info("chromadb_collections_recreated")


def create_vanna_client(
    model: str = DEFAULT_MODEL,
    ollama_host: str = DEFAULT_OLLAMA_HOST,
    chroma_host: str | None = None,
    chroma_port: int | None = None,
    chroma_collection: str = DEFAULT_CHROMA_COLLECTION,
    dialect: str = "SQL",
) -> MyVanna:
    """Factory function to create configured Vanna client."""
    config: dict = {
        "model": model,
        "ollama_host": ollama_host,
        "dialect": dialect,
    }

    if chroma_host:
        # Remote ChromaDB
        config["chroma_host"] = chroma_host
        if chroma_port:
            config["chroma_port"] = chroma_port
    # else: use local persistent ChromaDB

    config["collection_name"] = chroma_collection

    return MyVanna(config=config)

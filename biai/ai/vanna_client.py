"""Vanna.ai client with ChromaDB + Ollama integration."""

from vanna.chromadb import ChromaDB_VectorStore
from vanna.ollama import Ollama

from biai.config.constants import DEFAULT_MODEL
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


def create_vanna_client(
    model: str = DEFAULT_MODEL,
    ollama_host: str = "http://localhost:11434",
    chroma_host: str | None = None,
    chroma_port: int | None = None,
    chroma_collection: str = "biai_schema",
) -> MyVanna:
    """Factory function to create configured Vanna client."""
    config: dict = {
        "model": model,
        "ollama_host": ollama_host,
    }

    if chroma_host:
        # Remote ChromaDB
        config["chroma_host"] = chroma_host
        if chroma_port:
            config["chroma_port"] = chroma_port
    # else: use local persistent ChromaDB

    config["collection_name"] = chroma_collection

    return MyVanna(config=config)

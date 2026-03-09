import logging
import requests
import sys
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from config import DB_PATH, COLLECTION_NAME, EMBEDDING_MODEL, RETRIEVER_K

logger = logging.getLogger(__name__)

logger.info(f"Loading Chroma store: {DB_PATH}, collection: {COLLECTION_NAME}")


def check_ollama_health(timeout=5):
    """
    Check if Ollama is running and accessible.
    Raises SystemExit with clear error message if unavailable.
    """
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=timeout)
        if response.status_code == 200:
            logger.info("✓ Ollama is running and accessible")
            return True
    except (requests.ConnectionError, requests.Timeout) as e:
        logger.error(
            f"✗ CRITICAL: Cannot connect to Ollama at http://localhost:11434"
            f"\n\nOllama is required to run this application."
            f"\n\nHow to fix:"
            f"\n1. Download Ollama from https://ollama.com"
            f"\n2. Start Ollama: ollama serve"
            f"\n3. Pull the required model: ollama pull llama3.1"
            f"\n4. Then restart this application"
            f"\n\nError details: {str(e)}"
        )
        sys.exit(1)


# Verify Ollama is running BEFORE initializing embeddings
check_ollama_health()

embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

vectorstore = Chroma(
    persist_directory=DB_PATH,
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings,
)

count = len(vectorstore.get().get("ids", []))
logger.info(f"Stored vectors in Chroma: {count}")

retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K})

# ============= CONFIGURATION =============

DB_PATH = "./chroma_db_v4"
COLLECTION_NAME = "jio_knowledge_base"
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3.1"

HARMFUL_KEYWORDS = ["hack", "malware", "virus"]
JIO_KEYWORDS = [
    "jio", "fiber", "plan", "recharge", "network", "internet",
    "speed", "connectivity", "gateway", "sim", "data", "tariff"
]
KEYWORD_THRESHOLD = 2
MAX_REWRITES = 3
RETRIEVER_K = 3

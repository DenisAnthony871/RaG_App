CUSTOM_CORRECTIONS = {
    # Mobile
    "mobel": "mobile",
    "moble": "mobile",
    "moblie": "mobile",
    "mobiie": "mobile",
    "mobil": "mobile",

    # Network
    "ntwork": "network",
    "ntwrk": "network",
    "netwrk": "network",
    "netwerk": "network",
    "netowrk": "network",

    # Recharge
    "recharg": "recharge",
    "rechareg": "recharge",
    "rechrge": "recharge",
    "rcharge": "recharge",
    "recharje": "recharge",

    # Internet
    "interneet": "internet",
    "intrnet": "internet",
    "internt": "internet",
    "inernet": "internet",

    # Connection
    "conection": "connection",
    "connction": "connection",
    "connetion": "connection",
    "connecton": "connection",

    # Balance
    "balence": "balance",
    "ballance": "balance",
    "balace": "balance",

    # Validity
    "validty": "validity",
    "validy": "validity",
    "validiy": "validity",

    # SIM
    "simcard": "sim card",
    "sim-card": "sim card",

    # Jio specific
    "jiofiber": "jio fiber",
    "jiofibr": "jio fiber",
    "jiofibre": "jio fiber",
    "jiofibe": "jio fiber",
    "jio4g": "jio 4g",
    "jio5g": "jio 5g",

    # Signal
    "singal": "signal",
    "signel": "signal",
    "sinal": "signal",

    # Payment
    "paymet": "payment",
    "paymnt": "payment",
    "paiment": "payment",

    # Activate
    "activte": "activate",
    "actvate": "activate",
    "actiate": "activate",

    # Calling
    "callng": "calling",
    "caling": "calling",

    # Working
    "wrking": "working",
    "workng": "working",
    "wrk": "working",
}

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
MAX_REWRITES = 2
RETRIEVER_K = 3

# Jio RAG Support Agent

An AI-powered customer support chatbot for Jio services, built using LangGraph, LangChain, ChromaDB, and Ollama. The agent retrieves relevant information from a Jio knowledge base and generates accurate answers using a local LLM.

---

## Architecture

```
User Query
    ↓
Validate Input
    ↓
Enrich Context (Intent Detection)
    ↓
Force Retrieval (ChromaDB)
    ↓
Grade Documents (Keyword-based)
    ↓ relevant          ↓ not relevant
Generate Answer     Rewrite Question (max 2 rewrites)
    ↓
Format Answer
    ↓
Hallucination Check
    ↓
Final Response
```

---

## Tech Stack

- **LangGraph** — agent graph orchestration
- **LangChain** — LLM chains and tooling
- **ChromaDB** — vector store for knowledge base
- **Ollama** — local LLM (`llama3.1`) and embeddings (`nomic-embed-text`)
- **FastAPI** — REST API backend
- **Streamlit** — chat frontend

---

## Project Structure

```
project/
├── backend/
│   ├── main.py            # FastAPI app
│   ├── rag_graph.py       # Graph assembly
│   ├── nodes.py           # All graph node functions
│   ├── chains.py          # Rewrite chain
│   ├── tools.py           # Retriever tool
│   ├── database.py        # ChromaDB initialization
│   └── config.py          # Configuration constants
├── .env                   # API keys (not committed)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Prerequisites

- Python 3.12+
- [Ollama](https://ollama.com) installed and running
- Required Ollama models pulled:

```bash
ollama pull llama3.1
ollama pull nomic-embed-text
```

---

## Setup

**1. Clone the repo:**
```bash
git clone https://github.com/DenisAnthony871/RaG_App.git
cd RaG_App
```

**2. Create virtual environment:**
```bash
uv venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Mac/Linux
```

**3. Install dependencies:**
```bash
uv pip install -r requirements.txt
```

**4. Create `.env` file:**
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=Jio_RAG_Project
```

**5. Build the knowledge base:**

Run the indexing cells in `rag.ipynb` to populate ChromaDB with your Jio documents. The vector store will be saved to `./chroma_db_v4`.

---

## Running the Backend

```bash
cd backend
uvicorn main:app --host 127.0.0.1 --port 8080
```

API will be available at `http://127.0.0.1:8080`

Interactive docs at `http://127.0.0.1:8080/docs`

---

## API Endpoints

| Method | Endpoint  | Description                  |
|--------|-----------|------------------------------|
| GET    | /health   | Check if API is running      |
| GET    | /stats    | ChromaDB vector count        |
| POST   | /chat     | Send a query, get an answer  |

**Example request:**
```bash
curl -X POST http://127.0.0.1:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I fix slow internet on Jio Fiber?"}'
```

**Example response:**
```json
{
  "request_id": "a1b2c3d4",
  "answer": "To fix slow internet on Jio Fiber...",
  "status": "success",
  "response_time_ms": 4821.23
}
```

---

## Configuration

All key settings are in `backend/config.py`:

| Variable           | Default            | Description                        |
|--------------------|--------------------|------------------------------------|
| DB_PATH            | ./chroma_db_v4     | ChromaDB storage path              |
| LLM_MODEL          | llama3.1           | Ollama model for generation        |
| EMBEDDING_MODEL    | nomic-embed-text   | Ollama model for embeddings        |
| MAX_REWRITES       | 2                  | Max query rewrite attempts         |
| RETRIEVER_K        | 3                  | Number of docs to retrieve         |
| KEYWORD_THRESHOLD  | 2                  | Min keywords to consider relevant  |

---

## Notes

- ChromaDB folders are not committed to the repo — you must build the vector store locally by running the indexing notebook
- Ollama must be running before starting the API
- Keep `workers=1` in uvicorn since Ollama is single-threaded

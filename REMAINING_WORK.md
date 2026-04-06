# Jio RAG Project — Remaining Work

**Last Updated:** March 31, 2026
**Backend Status:** Production-Quality | **Frontend:** Not Started | **Tests:** Not Started

---

## Completed

### Backend Core
- FastAPI app with lifespan context manager
- 8-node LangGraph RAG pipeline (validate, enrich, retrieve, grade, rewrite, generate, format, hallucination check)
- ChromaDB vector store (`chroma_db_v4`, `nomic-embed-text` embeddings)
- `llama3.2:3b` LLM via Ollama
- SymSpell spell correction with 50+ Jio-specific custom corrections
- `better_profanity` profanity filter
- Harmful keyword filter (30+ terms)
- Short query allowlist (`5g`, `sim`, `jio`, etc.)
- Intent detection (troubleshooting / billing / informational)
- Document grading via JIO_KEYWORDS overlap (`KEYWORD_THRESHOLD=3`)
- Query rewriting (max 2 retries, `MAX_REWRITES=2`)
- JSON answer guard (try/except `json.loads`)
- Source attribution footer in `format_answer`
- Hallucination router (word overlap >= 5 with context)
- Fallback answer and graph exit for max-rewrite hits

### Auth and Security
- API key auth via `X-API-Key` header (`JIO_RAG_API_KEY` env var)
- `secrets.compare_digest()` — timing-safe comparison
- Invalid key logging with client IP (no PII from query logged)
- `.env.example` template for team onboarding

### Chat History (SQLite)
- `chat_history.py` — full implementation
- `conversations` and `messages` tables with FK and cascade delete
- Index on `conversation_id` for performance
- Functions: `init_db`, `create_conversation`, `conversation_exists`, `save_message`, `load_history`, `get_conversation_summary`, `delete_conversation`
- Chat history loaded and injected into graph on every `/chat` call
- `GET /conversations/{id}` — retrieve conversation and messages
- `DELETE /conversations/{id}` — safe delete with 404 on missing

### Infrastructure and Config
- Ollama health check on startup (`sys.exit(1)` with instructions if down)
- `.env` file with all required variables
- `.gitignore` — excludes `.env`, ChromaDB folders, notebooks, `__pycache__`, internal docs
- `requirements.txt` — fully populated
- `.vscode/settings.json` — env terminal injection
- `.rhdarc.json` — RHDA security scan configured
- Swagger UI at `/docs`
- Global exception handler returns 500 JSON

### Documentation
- `README.md` — setup guide, pipeline diagram, API reference, troubleshooting
- `REMAINING_WORK.md` — file-by-file status, current issues
- `BUG_REPORT.md` — all bugs tracked (5 fixed, 3 open)
- `TESTING_ENDPOINTS.md` — curl / Python / PowerShell examples

---

## Critical — Blocks Real Users

### 1. No Frontend UI

**Impact:** The chatbot is API-only — end users cannot interact with it directly
**Effort:** 3–5 days
**Recommended:** React + Vite SPA

```
[ ] Choose framework (React / Vue / Streamlit)
[ ] Design chat UI (input box, message history, typing indicator)
[ ] Wire to /chat endpoint with X-API-Key header
[ ] Display conversation_id for multi-turn sessions
[ ] Handle 401 / 500 errors gracefully in UI
[ ] Deploy frontend (Vercel or Netlify for quick MVP)
```

---

### 2. No Docker / Containerization

**Impact:** Cannot deploy to cloud without manual environment setup on each host
**Effort:** 1 day

```
[ ] Dockerfile for the FastAPI app
[ ] docker-compose.yml to orchestrate API + Ollama
[ ] .dockerignore (exclude chroma_db, .env, .venv, __pycache__)
[ ] Test: docker-compose up -> /health returns 200
[ ] Document docker setup in README
```

---

## High — Should Fix Before Any Team Growth

### 3. No Unit / Integration Tests

**Impact:** Risky to refactor or extend — no safety net
**Effort:** 2–3 days

```
[ ] pytest + pytest-asyncio setup (pytest.ini or pyproject.toml)
[ ] conftest.py — shared fixtures (mock graph, mock DB)
[ ] test_nodes.py:
    [ ] validate_input: harmful input, profanity, spell correction, short allowlist
    [ ] rewrite_question: max rewrite guard, appends not replaces
    [ ] generate_answer: JSON detection guard
    [ ] hallucination_router: low overlap triggers rewrite, high overlap exits
[ ] test_chat_history.py:
    [ ] create_conversation, save_message, load_history round-trip
    [ ] delete_conversation returns False for missing ID
[ ] test_main.py:
    [ ] /health returns 200 without auth
    [ ] /chat returns 401 without key
    [ ] /chat returns 200 with valid key and mocked graph
[ ] Target: 60%+ coverage
```

---

### 4. No Rate Limiting

**Impact:** A valid API key holder can send unlimited requests, blocking Ollama for other users
**Effort:** 2–4 hours

```
[ ] Add slowapi (FastAPI rate limit middleware)
[ ] Limit /chat to 10 requests per minute per API key or IP
[ ] Return 429 with Retry-After header on breach
```

Example:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address)

@app.post("/chat")
@limiter.limit("10/minute")
def chat(request: Request, ...):
    ...
```

---

## Important — Fix When There Is Time

### 5. CORS Open to All Origins

**File:** `main.py` L70
**Effort:** 15 minutes

```
[ ] Replace allow_origins=["*"] with actual frontend URL(s)
[ ] Add ALLOWED_ORIGINS to .env
[ ] Read from env in main.py
```

---

### 6. `check_ollama_health()` Called Twice

**File:** `database.py` L53
**Effort:** 5 minutes

```
[ ] Remove module-level check_ollama_health() call from database.py
[ ] Keep only the lifespan() call in main.py
```

---

### 7. Specific Exception Handling in `/chat`

**File:** `main.py` L166–168
**Effort:** 30 minutes

```
[ ] Split bare except Exception into IndexError, TimeoutError, Exception
[ ] Return appropriate HTTP status codes (500, 504)
[ ] See BUG #4 in BUG_REPORT.md for the code sample
```

---

### 8. `connection.py` — Delete or Document

**File:** `connection.py`
**Effort:** 15 minutes

```
[ ] Confirm no module imports connection.py
[ ] If unused -> delete file and commit
[ ] If intentional -> add docstring explaining its planned purpose
```

---

## Nice-to-Have (Future Phases)

| Feature | Impact | Effort |
|---------|--------|--------|
| Admin dashboard (conversation analytics) | Monitor usage | 3–5 days |
| Multi-language support | Wider audience | 2–3 days |
| Request caching (Redis or in-memory) | Reduce Ollama load | 1 day |
| A/B testing framework for prompts | Improve response quality | 2–3 days |
| Export conversations (JSON/CSV) | Data portability | 1 day |
| Webhook support (Slack, Teams) | Third-party integration | 1–2 days |

---

## Summary by Priority

| Priority | Count | Estimated Effort |
|----------|-------|-----------------|
| Complete | ~35 items | Done |
| Critical (blocks users) | 2 items | ~1 week |
| High (team scaling) | 2 items | ~3–4 days |
| Important (code quality) | 4 items | ~1–2 hours |
| Nice-to-have | 6 items | Future |

---

## File Checklist

**Core Backend** — all complete:
- `main.py` — FastAPI app, endpoints, auth, conversation wiring
- `rag_graph.py` — LangGraph graph assembly
- `nodes.py` — all 8 node functions and routing logic
- `chains.py` — rewrite chain and response model
- `tools.py` — retriever_tool with doc limit
- `database.py` — ChromaDB and Ollama health check
- `config.py` — all configuration constants
- `chat_history.py` — SQLite conversation history CRUD

**Config and Environment** — all complete:
- `.env`
- `.env.example`
- `.gitignore`
- `requirements.txt`
- `.vscode/settings.json`
- `.rhdarc.json`
- `connection.py` — orphaned, needs decision

**Tests** — none exist:
- `test_nodes.py` — not created
- `test_chat_history.py` — not created
- `test_main.py` — not created
- `conftest.py` — not created
- `pytest.ini` — not created

**Deployment** — none exist:
- `Dockerfile` — not created
- `docker-compose.yml` — not created
- `.dockerignore` — not created
- Cloud IaC (Terraform / Bicep) — not created

**Frontend** — nothing exists:
- No frontend directory or files

---

Total remaining effort to a production-ready app with frontend: approximately 2–3 weeks.

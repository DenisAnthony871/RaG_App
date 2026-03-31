# Jio RAG Project — Remaining Work

**Last Updated:** March 31, 2026
**Backend Status:** ✅ Production-Quality | **Frontend:** ❌ Not Started | **Tests:** ❌ Missing

---

## ✅ Completed

### Backend Core
- ✅ FastAPI app with lifespan context manager
- ✅ 8-node LangGraph RAG pipeline (validate → enrich → retrieve → grade → rewrite → generate → format → hallucination check)
- ✅ ChromaDB vector store (`chroma_db_v4`, `nomic-embed-text` embeddings)
- ✅ `llama3.2:3b` LLM via Ollama
- ✅ SymSpell spell correction with 50+ Jio-specific custom corrections
- ✅ `better_profanity` profanity filter
- ✅ Harmful keyword filter (30+ terms)
- ✅ Short query allowlist (`5g`, `sim`, `jio`, etc.)
- ✅ Intent detection (troubleshooting / billing / informational)
- ✅ Document grading via JIO_KEYWORDS overlap (`KEYWORD_THRESHOLD=3`)
- ✅ Query rewriting (max 2 retries, `MAX_REWRITES=2`)
- ✅ JSON answer guard (try/except `json.loads`)
- ✅ Source attribution footer in `format_answer`
- ✅ Hallucination router (word overlap ≥5 with context)
- ✅ Fallback answer + graph exit for max-rewrite hits

### Auth & Security
- ✅ API key auth via `X-API-Key` header (`JIO_RAG_API_KEY` env var)
- ✅ `secrets.compare_digest()` — timing-safe comparison
- ✅ Invalid key logging with client IP (no PII from query)
- ✅ `.env.example` template for team onboarding

### Chat History (SQLite)
- ✅ `chat_history.py` — full implementation
- ✅ `conversations` + `messages` tables with FK + cascade delete
- ✅ Index on `conversation_id` for performance
- ✅ `create_conversation`, `conversation_exists`, `save_message`, `load_history`, `get_conversation_summary`, `delete_conversation`
- ✅ Chat history loaded and injected into graph on every `/chat` call
- ✅ `GET /conversations/{id}` — retrieve conversation + messages
- ✅ `DELETE /conversations/{id}` — soft-safe delete with 404 on missing

### Infrastructure & Config
- ✅ Ollama health check on startup (`sys.exit(1)` with instructions if down)
- ✅ `.env` file with all required variables
- ✅ `.gitignore` — excludes `.env`, ChromaDB folders, notebooks, `__pycache__`
- ✅ `requirements.txt` — fully populated
- ✅ `.vscode/settings.json` — env terminal injection
- ✅ `.rhdarc.json` — RHDA security scan configured
- ✅ Swagger UI at `/docs`
- ✅ Global exception handler → 500 JSON

### Documentation
- ✅ `README.md` — setup guide, pipeline diagram, API reference, troubleshooting
- ✅ `PROJECT_STATUS.md` — this file (kept up to date)
- ✅ `BUG_REPORT.md` — all bugs tracked with status
- ✅ `TESTING_ENDPOINTS.md` — curl/Python/PowerShell examples

---

## 🔴 CRITICAL — Blocks Real Users

### 1. No Frontend UI
**Impact:** The chatbot is API-only — real users cannot use it  
**Effort:** 3–5 days  
**Recommended:** React + Vite SPA (fast to build, modern)

```
[ ] Choose framework (React/Vue/Streamlit)
[ ] Design chat UI (input box, message history, typing indicator)
[ ] Wire to /chat endpoint with X-API-Key header
[ ] Display conversation_id for multi-turn sessions
[ ] Handle 401 / 500 errors gracefully in UI
[ ] Deploy frontend (Vercel/Netlify for quick MVP)
```

---

### 2. No Docker / Containerization
**Impact:** Can't deploy to cloud without manual env setup  
**Effort:** 1 day

```
[ ] Dockerfile for the FastAPI app
[ ] docker-compose.yml to orchestrate API + Ollama
[ ] .dockerignore (exclude chroma_db, .env, .venv, __pycache__)
[ ] Test: docker-compose up → /health returns 200
[ ] Document docker setup in README
```

---

## 🟠 HIGH — Should Fix Before Any Team Growth

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
    [ ] hallucination_router: low overlap → rewrite, high overlap → end
[ ] test_chat_history.py:
    [ ] create_conversation, save_message, load_history
    [ ] delete_conversation returns False for missing ID
[ ] test_main.py:
    [ ] /health → 200 no auth
    [ ] /chat → 401 without key
    [ ] /chat → 200 with valid key + mock graph
[ ] Target: 60%+ coverage
```

---

### 4. No Rate Limiting
**Impact:** A valid API key holder can send unlimited requests, hammering Ollama  
**Effort:** 2–4 hours

```
[ ] Add slowapi (FastAPI rate limit middleware)
[ ] Limit /chat to 10 req/min per API key or IP
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

## 🟡 IMPORTANT — Fix When There's Time

### 5. CORS Open to All Origins
**File:** `main.py` L70  
**Effort:** 15 minutes

```
[ ] Replace allow_origins=["*"] with actual frontend URL(s)
[ ] Add to .env: ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
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
[ ] See BUG #4 in BUG_REPORT.md for code sample
```

---

### 8. `connection.py` — Delete or Document
**File:** `connection.py`  
**Effort:** 15 minutes

```
[ ] Confirm no module imports connection.py (grep -r "from connection import")
[ ] If unused → delete file and commit
[ ] If intentional → add docstring explaining its planned purpose
```

---

### 9. Update README Model Name
**File:** `README.md` L57  
**Effort:** 5 minutes

```
[ ] Change "llama3.1" → "llama3.2:3b" in tech stack table and ollama pull command
```

---

## 🟢 NICE-TO-HAVE (Future Phases)

| Feature | Impact | Effort |
|---------|--------|--------|
| Admin dashboard (conversation analytics) | Monitor usage | 3–5 days |
| Multi-language support | Wider audience | 2–3 days |
| Request caching (Redis / in-memory) | Reduce Ollama load | 1 day |
| A/B testing framework for prompts | Improve quality | 2–3 days |
| Export conversations (JSON/CSV) | Data portability | 1 day |
| Webhook support (Slack, Teams) | Integration | 1–2 days |
| Model fine-tuning UI | Better answers | 3–5 days |

---

## 📊 Summary by Priority

| Priority | Count | ETA |
|----------|-------|-----|
| ✅ Complete | ~35 items | Done |
| 🔴 Critical (blocks users) | 2 items | ~1 week |
| 🟠 High (team scaling) | 2 items | ~3–4 days |
| 🟡 Important (code quality) | 5 items | ~2–3 hours |
| 🟢 Nice-to-have | 7 items | Future |

---

## 📁 File Checklist

**Core Backend** — all complete:
- ✅ `main.py` — FastAPI app, endpoints, auth, conversation wiring
- ✅ `rag_graph.py` — LangGraph graph assembly
- ✅ `nodes.py` — all 8 node functions + routing logic
- ✅ `chains.py` — rewrite chain + response model
- ✅ `tools.py` — retriever_tool with doc limit
- ✅ `database.py` — ChromaDB + Ollama health check
- ✅ `config.py` — all configuration constants
- ✅ `chat_history.py` — SQLite conversation history CRUD

**Config & Environment** — all complete:
- ✅ `.env`
- ✅ `.env.example`
- ✅ `.gitignore`
- ✅ `requirements.txt`
- ✅ `.vscode/settings.json`
- ✅ `.rhdarc.json`
- ⚠️ `connection.py` — orphaned, needs decision

**Documentation** — mostly complete:
- ✅ `README.md` (minor: model name outdated)
- ✅ `PROJECT_STATUS.md`
- ✅ `BUG_REPORT.md`
- ✅ `TESTING_ENDPOINTS.md`
- ❌ `API_GUIDE.md` — not created
- ❌ `DEPLOYMENT.md` — not created

**Tests** — none exist:
- ❌ `test_nodes.py`
- ❌ `test_chat_history.py`
- ❌ `test_main.py`
- ❌ `conftest.py`
- ❌ `pytest.ini`

**Deployment** — none exist:
- ❌ `Dockerfile`
- ❌ `docker-compose.yml`
- ❌ `.dockerignore`
- ❌ Cloud IaC (Terraform / Bicep)

**Frontend** — nothing exists:
- ❌ Any frontend directory or files

---

**Total remaining effort to production-ready app with frontend: ~2–3 weeks**

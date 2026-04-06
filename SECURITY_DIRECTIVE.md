# Security Hardening Directive — Jio RAG Chatbot

**Project:** Jio RAG chatbot — FastAPI + LangGraph + ChromaDB + Ollama (`llama3.2:3b`) + SQLite  
**Task:** Security hardening across multiple files. Implement exactly what is listed below, nothing more.  
**Files to modify:** `config.py`, `nodes.py`, `main.py`, `chains.py`, `.env.example`, `BUG_REPORT.md`  
**Files to return:** All six files above.

---

## File 1 — `config.py`

Add these two constants at the bottom of the file:

```python
MAX_HISTORY_TURNS = 5        # retain only last 5 turns (10 messages) of conversation
MAX_REQUEST_SIZE_BYTES = 2 * 1024 * 1024  # 2MB request size limit
```

---

## File 2 — `nodes.py`

In `validate_input`, implement a defense-in-depth approach for prompt injection (replacing the static INJECTION_PHRASES list):

1. **Robust Input Normalization**: Add Unicode normalization, remove homoglyphs, collapse whitespace and obfuscating punctuation, and decode common encodings.
2. **Regex-based Detection**: Run a regex-based fuzzy/pattern detector rather than exact substring matches for known injection phrases.
3. **Intent Classifier**: Add a secondary step that flags suspicious intent via a lightweight classifier or heuristic (e.g., high ratio of imperative verbs or repeated instruction tokens) and returns the safe AIMessage refusal.
4. **Boundary Enforcement**: Ensure outputs enforce system message boundaries. 
5. **Telemetry**: Add logging/metrics for detected attempts so monitoring can catch bypasses.

---

## File 3 — `main.py`

### 3a. Add imports

Add after existing imports:

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
```

### 3b. Add environment reads

Add after `API_KEY = os.getenv("JIO_RAG_API_KEY")`:

```python
from config import MAX_REQUEST_SIZE_BYTES
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
```

### 3c. Add request size limit middleware class

Add before `lifespan`:

```python
class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE_BYTES:
            return Response(content='{"detail": "Request too large"}', status_code=413, media_type="application/json")
            
        body = b""
        async for chunk in request.stream():
            body += chunk
            if len(body) > MAX_REQUEST_SIZE_BYTES:
                host = request.client.host if request.client else "unknown"
                logger.warning(f"Request too large (streamed) | IP: {host}")
                return Response(
                    content='{"detail": "Request too large"}',
                    status_code=413,
                    media_type="application/json",
                )
        
        # Re-supply the body to downstream handlers using Starlette's documented receive pattern
        async def receive():
            return {"type": "http.request", "body": body}
        request._receive = receive
        
        return await call_next(request)
```

### 3d. Replace CORS middleware block

Replace the existing `CORSMiddleware` and `SlowAPIMiddleware` lines with:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST", "GET", "DELETE"],
    allow_headers=["*"],
)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
```

### 3e. Update config import

Add `MAX_HISTORY_TURNS` to the import from config:

```python
from config import DB_PATH, COLLECTION_NAME, MAX_HISTORY_TURNS
```

### 3f. Replace history loading block in `/chat`

Find:

```python
history = load_history(conversation_id)
messages = []
for msg in history:
    if msg["role"] == "human":
        messages.append(HumanMessage(content=msg["content"]))
    elif msg["role"] == "ai":
        messages.append(AIMessage(content=msg["content"]))
```

Replace with:

```python
history = load_history(conversation_id)
# Trim to last MAX_HISTORY_TURNS turns (2 messages per turn)
max_messages = MAX_HISTORY_TURNS * 2
history = history[-max_messages:] if len(history) > max_messages else history
messages = []
for msg in history:
    if msg["role"] == "human":
        messages.append(HumanMessage(content=msg["content"]))
    elif msg["role"] == "ai":
        messages.append(AIMessage(content=msg["content"]))
```

### 3g. Split generic exception handler in `/chat`

Replace:

```python
except Exception as e:
    logger.error(f"[{request_id}] Error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Failed to process query")
```

With:

```python
import concurrent.futures
from httpx import ReadTimeout

# ... inside handler ...
except IndexError:
    logger.error(f"[{request_id}] Graph state error", exc_info=True)
    raise HTTPException(status_code=500, detail="Invalid graph state")
except Exception as e:
    # use specific LLM library timeout instead if possible!
    if isinstance(e, (TimeoutError, ReadTimeout, concurrent.futures.TimeoutError)):
        logger.error(f"[{request_id}] LLM processing timeout", exc_info=True)
        raise HTTPException(status_code=504, detail="Processing timeout")
    logger.error(f"[{request_id}] Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal error")
```

---

## File 4 — `chains.py`

Add a timeout to the Ollama model instance. Replace:

```python
response_model = ChatOllama(model=LLM_MODEL)
```

With:

```python
response_model = ChatOllama(model=LLM_MODEL, timeout=60)
```

---

## File 5 — `.env.example`

Add this entry:

```
# Comma-separated list of allowed frontend origins
# Example: ALLOWED_ORIGINS=https://yourapp.com,http://localhost:3000
ALLOWED_ORIGINS=http://localhost:3000
```

---

## File 6 — `BUG_REPORT.md`

Add this entry to the Open Bugs section:

```
### BUG #9: No Tenant Isolation on Conversation Endpoints — OPEN
**File:** main.py | **Severity:** High (for multi-user production)

**Problem:** Conversations returned by the GET/DELETE /conversations/{id} handlers in main.py are not tenant-isolated. Any client with a valid API key can read or delete any conversation.

**Recommended Fix:** 
1. Update Conversation storage schema to include `owner_id`.
2. Enforce ownership checks in the conversation read/delete handlers (GET/DELETE /conversations/{id}).
3. Ensure API key lookup maps to a specific user before returning or deleting a conversation (validating the requesting key’s owner against `conversation.owner_id`).
4. Add startup validation to detect multiple API keys and hard-fail if multi-key usage is present natively. Emit runtime warnings when multiple distinct keys or multi-user patterns are observed.

**Implementation Timeline TODO:**
- [ ] Add `owner_id` to schema
- [ ] Route `owner_id` through handlers
- [ ] Add multi-key detection at app startup
- [ ] Update tests for conversation access and startup key validation
```

---

## Verification Steps

After applying all changes, verify the following manually:

1. **Request size** — Send POST payload >2MB with missing or tampered Content-Length headers to `/chat` and verify blocked.
2. **CORS** — confirm `ALLOWED_ORIGINS` in `.env` is read correctly for endpoints.
3. **Context compression** — verify history trimming over 10 messages.
4. **Prompt injection** — expand to include obfuscated and multi-turn injections (character substitution, encoding, split-turn attacks) against the prompt filtering logic.
5. **Exception handler** — temporarily raise a `ValueError` inside the `/chat` request handler and confirm the application maps that exception to an HTTP 500 response. Separately, configure Ollama with a 1s timeout and send a complex query to confirm that `chains.py` surfaces the timeout as an HTTP 504.
6. **Tenant isolation** — create a conversation under one API key and attempt `GET /conversations/{id}` with a different key to confirm isolation. Ensure testers are explicitly routed via the endpoint URLs and `ALLOWED_ORIGINS`.

---

## Notes

- Do not implement multi-tenant auth — BUG #9 is documented as a known limitation only
- Do not modify `rag_graph.py`, `tools.py`, `database.py`, or `chat_history.py`
- Do not add any features beyond what is listed above

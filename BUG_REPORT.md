# Bug Report — Jio RAG Support Agent

**Last Updated:** March 31, 2026
**Severity Levels:** Critical | High | Medium | Low

---

## Resolved Bugs

### BUG #1: Message History Loss in `validate_input` — FIXED

**File:** `nodes.py` | **Was:** Critical

**Problem:**

```python
corrected_messages = [HumanMessage(content=corrected)]
return {"messages": corrected_messages}  # Replaced ALL messages
```

**Fix Applied:**

```python
messages[-1] = HumanMessage(content=corrected)
return {"messages": messages}  # Replaces only last message
```

---

### BUG #2: Message History Loss in `rewrite_question` — FIXED

**File:** `nodes.py` | **Was:** Critical

**Problem:**

```python
return {"messages": [HumanMessage(content=better_question)]}  # Dropped all context
```

**Fix Applied:**

```python
messages.append(HumanMessage(content=better_question))
return {"messages": messages, "rewrite_count": rewrite_count + 1}
```

---

### BUG #3: Unsafe Vectorstore Access in `/stats` — FIXED

**File:** `main.py` | **Was:** High

**Problem:**

```python
count = len(vectorstore.get().get("ids", []))  # Crashes if .get() returns None
```

**Fix Applied:**

```python
result = vectorstore.get()
count = len(result.get("ids", []) if result else [])
```

---

### BUG #5: Incomplete JSON Detection in `generate_answer` — FIXED

**File:** `nodes.py` | **Was:** Medium

**Problem:**

```python
if answer.strip().startswith("{"):  # Missed arrays, spaced braces
```

**Fix Applied:**

```python
try:
    json.loads(answer)
    answer = "I don't have enough information to answer that question."
except (json.JSONDecodeError, ValueError):
    pass
```

---

### BUG #6: No Result Limit in `retriever_tool` — FIXED

**File:** `tools.py` | **Was:** Low

**Fix Applied:**

```python
docs_limited = docs[:5]
return "\n".join([f"[{i+1}] {doc.page_content}" for i, doc in enumerate(docs_limited)])
```

---

### BUG #7: `check_ollama_health()` Called Twice at Startup — FIXED

**File:** `database.py` | **Was:** Low

**Problem:** Called at module import time in `database.py` and again in `lifespan()` in `main.py`. Two HTTP requests to Ollama on every startup; also fired during import-time test setup.

**Fix Applied:** Module-level call removed from `database.py`. Single canonical call site is `lifespan()` in `main.py`. Comment in `database.py` explains absence.

---

### BUG #9: State Mutation in Conditional Edge Router — FIXED

**File:** `nodes.py` | **Was:** High

**Problem:** `hallucination_router` was a conditional edge routing function that directly mutated state:

```python
state["confidence"] = confidence  # Silently fails — routers cannot update state in LangGraph
```

Routers must return a string. State updates must come from node return values. Confidence was never actually written to the result that `main.py` reads.

**Fix Applied:** Split into two separate functions:

1. `check_hallucination(state: JioState) -> dict` — registered as a node, computes confidence and returns `{"confidence": confidence}` as a proper state update.
2. `hallucination_router(state: JioState) -> str` — pure router, reads state only, returns `"end"` or `"rewrite_question"`.

`rag_graph.py` updated:

```text
format_answer -> check_hallucination (node) -> hallucination_router (conditional edge)
```

---

### BUG #10: `rewrite_count` Derived from Message Count — FIXED

**File:** `nodes.py` | **Was:** Medium

**Problem:**

```python
rewrite_count = sum(1 for msg in messages if msg.type == "human") - 1
```

Counted human messages in the list to infer rewrite count — fragile, breaks when conversation history is loaded (prior human messages from SQLite inflate the count).

**Fix Applied:** `rewrite_count` is now an explicit field in `JioState`, initialised to `0` in `graph.invoke`, incremented by `rewrite_question` on each rewrite:

```python
rewrite_count = state.get("rewrite_count", 0)
...
return {"messages": messages, "rewrite_count": rewrite_count + 1}
```

---

### BUG #4: Generic Exception Handler in Chat Endpoint — FIXED

**File:** `main.py` | **Was:** Medium

**Problem:** All graph errors produce the same HTTP 500:

```python
except Exception as e:
    raise HTTPException(status_code=500, detail="Failed to process query")
```

**Fix Applied:** Split the generic block into specific exceptions for `IndexError` (500), `TimeoutError` (504), `ValueError` (400), and a fallback `Exception`.

---

### BUG #8: CORS Open to All Origins — FIXED

**File:** `main.py` | **Was:** High (for production)

**Problem:**

```python
allow_origins=["*"],  # Any origin can call this API
```

**Fix Applied:** Locked down origins by configuring `allow_origins=ALLOWED_ORIGINS` mapped to an environment variable.

---

## Open Bugs

### BUG #12: No Tenant Isolation on Conversation Endpoints — OPEN

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

---

## Bug Summary

| Bug # | Severity | Description | Status |
| ----- | -------- | ----------- | ------ |
| #1 | Critical | `validate_input` replaced full message history | Fixed |
| #2 | Critical | `rewrite_question` dropped all context | Fixed |
| #3 | High | Unsafe chained `.get()` in `/stats` | Fixed |
| #4 | Medium | Generic `except Exception` hides error types | Fixed |
| #5 | Medium | `startswith("{")` missed arrays and spaced JSON | Fixed |
| #6 | Low | No doc limit in `retriever_tool` | Fixed |
| #7 | Low | `check_ollama_health()` called twice on startup | Fixed |
| #8 | High | CORS `allow_origins=["*"]` — open to all origins | Fixed |
| #9 | High | Router mutated state directly — confidence never persisted | Fixed |
| #10 | Medium | `rewrite_count` inferred from message count (broke with history) | Fixed |
| #12 | High | No tenant isolation on conversation endpoints | Open |

---
1 bug remains open. BUG #12 must be resolved before any public multi-tenant deployment.

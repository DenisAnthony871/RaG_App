# Bug Report — Jio RAG Support Agent

**Last Updated:** March 31, 2026
**Severity Levels:** 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low

---

## ✅ Resolved Bugs (All Fixed)

### BUG #1: Message History Loss in `validate_input` ✅ FIXED
**File:** `nodes.py` | **Was:** 🔴 Critical

**Was:**
```python
corrected_messages = [HumanMessage(content=corrected)]
return {"messages": corrected_messages}  # ❌ Replaced ALL messages
```
**Fix Applied:**
```python
messages[-1] = HumanMessage(content=corrected)
return {"messages": messages}  # ✅ Replaces only last message
```

---

### BUG #2: Message History Loss in `rewrite_question` ✅ FIXED
**File:** `nodes.py` | **Was:** 🔴 Critical

**Was:**
```python
return {"messages": [HumanMessage(content=better_question)]}  # ❌ Dropped all context
```
**Fix Applied:**
```python
messages.append(HumanMessage(content=better_question))
return {"messages": messages}  # ✅ Appends rewritten question
```

---

### BUG #3: Unsafe Vectorstore Access in `/stats` ✅ FIXED
**File:** `main.py` | **Was:** 🟠 High

**Was:**
```python
count = len(vectorstore.get().get("ids", []))  # ❌ Crashes if .get() returns None
```
**Fix Applied:**
```python
result = vectorstore.get()
count = len(result.get("ids", []) if result else [])  # ✅ Safe null check
```

---

### BUG #5: Incomplete JSON Detection in `generate_answer` ✅ FIXED
**File:** `nodes.py` | **Was:** 🟡 Medium

**Was:**
```python
if answer.strip().startswith("{"):
    answer = "I don't have enough information..."  # ❌ Missed arrays, spaced braces
```
**Fix Applied:**
```python
try:
    json.loads(answer)
    answer = "I don't have enough information to answer that question."
except (json.JSONDecodeError, ValueError):
    pass  # ✅ Catches all valid JSON including arrays
```

---

### BUG #6: No Result Limit in `retriever_tool` ✅ FIXED
**File:** `tools.py` | **Was:** 🟢 Low

**Was:**
```python
return "\n".join([doc.page_content for doc in docs])  # ❌ No limit, raw content
```
**Fix Applied:**
```python
docs_limited = docs[:5]
return "\n".join([f"[{i+1}] {doc.page_content}" for i, doc in enumerate(docs_limited)])  # ✅ Top 5, numbered
```

---

## 🟡 Open Bugs / Issues

### BUG #4: Generic Exception Handler in Chat Endpoint — OPEN
**File:** `main.py` L166-168 | **Severity:** 🟡 Medium

**Problem:** All errors from the graph are caught by one bare `except Exception`:
```python
except Exception as e:
    logger.error(f"[{request_id}] Error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Failed to process query")
```
- `IndexError` (missing tool results), `ValueError` (empty messages), LLM timeout — all look the same from the outside
- Makes debugging in production difficult

**Recommended Fix:**
```python
except IndexError:
    logger.error(f"[{request_id}] Graph state error — missing expected message")
    raise HTTPException(status_code=500, detail="Invalid graph state")
except TimeoutError:
    logger.error(f"[{request_id}] LLM processing timeout")
    raise HTTPException(status_code=504, detail="Processing timeout")
except Exception as e:
    logger.error(f"[{request_id}] Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal error")
```

---

### BUG #7: `check_ollama_health()` Called Twice at Startup — OPEN
**File:** `database.py` L53 + `main.py` L60 | **Severity:** 🟢 Low

**Problem:** `check_ollama_health()` is called at module import time in `database.py` (line 53), and then again explicitly in the `lifespan()` function in `main.py` (line 60). This causes two HTTP requests to Ollama on every startup.

**Recommended Fix:** Remove the module-level call in `database.py` and rely solely on `lifespan()`:
```python
# database.py — remove this line:
check_ollama_health()  # ❌ Called again in lifespan already
```

---

### BUG #8: CORS Open to All Origins — OPEN
**File:** `main.py` L70 | **Severity:** 🟠 High (for production)

**Problem:**
```python
allow_origins=["*"],  # ⚠️ Any origin can call this API
```
The existing TODO comment acknowledges this. With API key auth in place, the risk is lower, but it's still a security bad practice.

**Recommended Fix:**
```python
allow_origins=["http://localhost:3000", "https://your-frontend-domain.com"],
```

---

## 📊 Bug Summary Table

| Bug # | Severity | Description | Status |
|-------|----------|-------------|--------|
| #1 | 🔴 Critical | `validate_input` replaced full message history | ✅ Fixed |
| #2 | 🔴 Critical | `rewrite_question` dropped all context | ✅ Fixed |
| #3 | 🟠 High | Unsafe chained `.get()` in `/stats` | ✅ Fixed |
| #4 | 🟡 Medium | Generic `except Exception` hides error types | 🔴 Open |
| #5 | 🟡 Medium | `startswith("{")` missed arrays and spaced JSON | ✅ Fixed |
| #6 | 🟢 Low | No doc limit in `retriever_tool` | ✅ Fixed |
| #7 | 🟢 Low | `check_ollama_health()` called twice on startup | 🔴 Open |
| #8 | 🟠 High | CORS `allow_origins=["*"]` in production | 🔴 Open |

---

**3 bugs remain open. None are blocking for development — but #8 must be fixed before public production deployment.**

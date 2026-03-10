# Bug Report - Jio RAG Support Agent

**Date:** March 10, 2026  
**Severity Levels:** 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low

---

## 🐛 Bugs Found

### BUG #1: Message History Loss in `validate_input` 🔴 CRITICAL

**File:** [nodes.py](nodes.py#L28-L47)  
**Severity:** Critical - Breaks conversation context

**Problem:**

```python
# Current buggy code
corrected_messages = [HumanMessage(content=corrected)]
return {"messages": corrected_messages}  # ❌ Replaces ALL messages
```

This completely replaces the message history with just the corrected message. All previous AI responses, tool results, and context are lost.

**Impact:**
- Graph cannot track rewrite count (rewrite_question will always think rewrite_count = 0)
- Conversation history is broken
- Hallucination router cannot find tool results to validate context

**Fix:** Append corrected message instead of replacing:

```python
messages[-1] = HumanMessage(content=corrected)
return {"messages": messages}
```

---

### BUG #2: Message History Loss in `rewrite_question` 🔴 CRITICAL

**File:** [nodes.py](nodes.py#L104-L122)  
**Severity:** Critical - Breaks graph flow

**Problem:**

```python
return {"messages": [HumanMessage(content=better_question)]}  # ❌ Loses all context
```

This replaces all messages with just the rewritten question. Loses:
- Original question
- Retrieved documents (tool results)
- Previous AI responses

**Impact:**
- Tool results from retrieval are lost
- Answer generation fails (can't find tool message for context)
- Graph resets unnecessarily

**Fix:** Append the rewritten question:

```python
messages.append(HumanMessage(content=better_question))
return {"messages": messages}
```

---

### BUG #3: Unsafe Vectorstore Access in `/stats` Endpoint 🟠 HIGH

**File:** [main.py](main.py#L70-L76)  
**Severity:** High - Can crash endpoint

**Problem:**

```python
count = len(vectorstore.get().get("ids", []))  # Chains .get() calls unsafely
```

If `vectorstore.get()` returns `None`, calling `.get("ids", [])` on None will crash.

**Fix:**

```python
result = vectorstore.get()
count = len(result.get("ids", []) if result else [])
```

---

### BUG #4: Incomplete Error Handling in Chat Endpoint 🟡 MEDIUM

**File:** [main.py](main.py#L87-D101)  
**Severity:** Medium - Hides root cause

**Problem:**

```python
except Exception as e:
    logger.error(f"[{request_id}] Error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Failed to process query")
```

Generic exception handler doesn't distinguish between:
- Missing tool results (returns IndexError)
- Empty messages (returns ValueError)
- LLM timeout
- Graph execution errors

This masks the real issue from debugging.

**Fix:** Add specific exception handling:

```python
except IndexError:
    logger.error(f"[{request_id}] Index error - missing expected message")
    raise HTTPException(status_code=500, detail="Invalid graph state")
except TimeoutError:
    logger.error(f"[{request_id}] LLM timeout")
    raise HTTPException(status_code=504, detail="Processing timeout")
except Exception as e:
    logger.error(f"[{request_id}] Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal error")
```

---

### BUG #5: Missing Error Handling in `generate_answer` 🟡 MEDIUM

**File:** [nodes.py](nodes.py#L148-L169)  
**Severity:** Medium - Can return malformed JSON as real answer

**Problem:**

```python
if answer.strip().startswith("{"):
    answer = "I don't have enough information..."
```

Only checks if answer starts with `{`. If LLM returns:
- `[{"key": "value"}]` - starts with `[`, bypasses check
- `{ "key": "value" }` (with space) - starts with space, also fails

**Fix:** Use try-except for JSON:

```python
try:
    json.loads(answer)
    # If that succeeded, it's JSON - reject it
    answer = "I don't have enough information..."
except ValueError:
    # Not JSON, safe to use answer
    pass
```

---

### BUG #6: Inefficient String Joining in `/stats` 🟢 LOW

**File:** [tools.py](tools.py#L6)  
**Severity:** Low - Performance issue with large results

**Problem:**

```python
return "\n".join([doc.page_content for doc in docs]) if docs else "No results found"
```

For 100+ documents, this creates a very long string. Better to limit results or use pagination.

**Fix:**

```python
docs_limited = docs[:5]  # Limit to top 5 most relevant
return "\n".join([f"[{i+1}] {doc.page_content}" for i, doc in enumerate(docs_limited)]) if docs_limited else "No results found"
```

---

## 🛠️ Summary

| Bug # | Severity | Impact | Status |
|-------|----------|--------|--------|
| #1 | 🔴 Critical | Message history loss | Needs immediate fix |
| #2 | 🔴 Critical | Context loss in rewrite | Needs immediate fix |
| #3 | 🟠 High | /stats endpoint crash | Should fix |
| #4 | 🟡 Medium | Poor debugging | Nice to have |
| #5 | 🟡 Medium | JSON detection bug | Should fix |
| #6 | 🟢 Low | Performance issue | Can defer |

---

**Recommendation:** Fix bugs #1-2 immediately before deployment. They break core functionality.

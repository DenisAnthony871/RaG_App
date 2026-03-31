# API Testing Guide — Jio RAG Support Agent

**Last Updated:** March 31, 2026
**Base URL:** `http://127.0.0.1:8080`
**Auth:** All endpoints except `/health` require the `X-API-Key` header

---

## Prerequisites

1. Ollama running — `ollama serve` in a separate terminal
2. API running — `python main.py` (starts on `0.0.0.0:8080`)
3. API key — set `JIO_RAG_API_KEY=your-key` in `.env`
4. ChromaDB populated — run `rag.ipynb` first to build the vector store

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Server liveness check |
| GET | `/stats` | Required | Vector store document count |
| POST | `/chat` | Required | Send a query, get an answer |
| GET | `/conversations/{id}` | Required | Get conversation history |
| DELETE | `/conversations/{id}` | Required | Delete a conversation |

---

## 1. Health Check — No Auth Required

Confirm the API is running.

```bash
curl http://127.0.0.1:8080/health
```

**Expected:**
```json
{"status": "healthy"}
```

---

## 2. Vector Store Stats — Auth Required

Check how many documents are in ChromaDB.

```bash
curl http://127.0.0.1:8080/stats \
  -H "X-API-Key: YOUR_API_KEY"
```

**Expected:**
```json
{
  "total_vectors": 842,
  "collection": "jio_knowledge_base",
  "db_path": "./chroma_db_v4"
}
```

---

## 3. Chat — New Conversation

Start a fresh conversation. The API auto-creates a `conversation_id` and returns it in the response.

```bash
curl -X POST http://127.0.0.1:8080/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"query": "What is Jio Fiber?"}'
```

**Expected:**
```json
{
  "request_id": "a1b2c3d4",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "answer": "Jio Fiber is a high-speed broadband service...\n\n---\n**Sources:** Retrieved from Jio Knowledge Base\nInformation verified from retrieved documents",
  "status": "success",
  "response_time_ms": 3241.87
}
```

Save the `conversation_id` to continue the same conversation in subsequent requests.

---

## 4. Chat — Continue a Conversation (Multi-turn)

Pass the `conversation_id` from a previous response to maintain context.

```bash
curl -X POST http://127.0.0.1:8080/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "query": "What plans does it offer?",
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

If the `conversation_id` does not exist, the API returns `404 Conversation not found`.

---

## 5. Chat — Troubleshooting Query

```bash
curl -X POST http://127.0.0.1:8080/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"query": "How do I fix slow internet on Jio Fiber?"}'
```

---

## 6. Chat — Spell Correction Demo

The input validator corrects common typos before processing. These queries should resolve correctly:

```bash
curl -X POST http://127.0.0.1:8080/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"query": "how fast is jiofiber interneet speed"}'
```

`jiofiber` -> `Jio Fiber`, `interneet` -> `internet`

---

## 7. Get Conversation History

Retrieve all messages in a conversation.

```bash
curl http://127.0.0.1:8080/conversations/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: YOUR_API_KEY"
```

**Expected:**
```json
{
  "conversation": {
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2026-03-31T05:10:00.000Z",
    "updated_at": "2026-03-31T05:12:00.000Z",
    "message_count": 4
  },
  "messages": [
    {"role": "human", "content": "What is Jio Fiber?", "timestamp": "2026-03-31T05:10:00.000Z"},
    {"role": "ai", "content": "Jio Fiber is...", "timestamp": "2026-03-31T05:10:03.000Z"}
  ]
}
```

---

## 8. Delete Conversation

```bash
curl -X DELETE http://127.0.0.1:8080/conversations/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: YOUR_API_KEY"
```

**Expected:**
```json
{"status": "deleted", "conversation_id": "550e8400-e29b-41d4-a716-446655440000"}
```

---

## Error Responses

| HTTP Code | Cause | Fix |
|-----------|-------|-----|
| `401 Unauthorized` | Missing or wrong `X-API-Key` | Check your key in `.env` |
| `404 Not Found` | Unknown `conversation_id` | Use a valid ID or omit it to start fresh |
| `422 Unprocessable Entity` | Query too short (<3 chars) or too long (>500) | Adjust query length |
| `500 Internal Server Error` | Ollama crashed or graph error | Check `ollama serve` is running |
| `500 Server misconfiguration` | `JIO_RAG_API_KEY` not set in `.env` | Add key to `.env` and restart |

---

## Using PowerShell (Windows)

```powershell
$headers = @{
    "Content-Type" = "application/json"
    "X-API-Key"    = "YOUR_API_KEY"
}

# Health check (no auth needed)
Invoke-RestMethod -Uri "http://127.0.0.1:8080/health" -Method Get

# Stats
Invoke-RestMethod -Uri "http://127.0.0.1:8080/stats" -Method Get -Headers $headers

# Chat
$body = '{"query": "What is Jio Fiber?"}'
Invoke-RestMethod -Uri "http://127.0.0.1:8080/chat" -Method Post -Headers $headers -Body $body
```

---

## Using Python Requests

```python
import requests

BASE_URL = "http://127.0.0.1:8080"
API_KEY  = "YOUR_API_KEY"
HEADERS  = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

# Health check
print(requests.get(f"{BASE_URL}/health").json())

# Start new conversation
resp = requests.post(f"{BASE_URL}/chat", json={"query": "What is Jio Fiber?"}, headers=HEADERS)
data = resp.json()
print(data["answer"])

conversation_id = data["conversation_id"]

# Follow-up in same conversation
resp2 = requests.post(
    f"{BASE_URL}/chat",
    json={"query": "What plans are available?", "conversation_id": conversation_id},
    headers=HEADERS
)
print(resp2.json()["answer"])
```

---

## Batch Test Script (PowerShell)

Save as `test_api.ps1` and run with `.\test_api.ps1`:

```powershell
$BASE = "http://127.0.0.1:8080"
$KEY  = "YOUR_API_KEY"
$AUTH = @{"X-API-Key" = $KEY; "Content-Type" = "application/json"}

Write-Host "=== Jio RAG API Tests ==="

Write-Host "`n1. Health Check"
Invoke-RestMethod -Uri "$BASE/health" -Method Get | ConvertTo-Json

Write-Host "`n2. Stats"
Invoke-RestMethod -Uri "$BASE/stats" -Method Get -Headers $AUTH | ConvertTo-Json

Write-Host "`n3. Chat: What is Jio Fiber?"
$r = Invoke-RestMethod -Uri "$BASE/chat" -Method Post -Headers $AUTH -Body '{"query":"What is Jio Fiber?"}'
$r | ConvertTo-Json

Write-Host "`n4. Multi-turn follow-up"
$cid = $r.conversation_id
$body = "{`"query`":`"What plans does it offer?`",`"conversation_id`":`"$cid`"}"
Invoke-RestMethod -Uri "$BASE/chat" -Method Post -Headers $AUTH -Body $body | ConvertTo-Json

Write-Host "`n=== Tests Complete ==="
```

---

## Swagger UI

Interactive API docs are available at `http://127.0.0.1:8080/docs`.

Use the **Authorize** button (top-right of the Swagger page) to enter your `X-API-Key` before testing protected endpoints.

---

## Performance Reference

| Condition | Expected Response Time |
|-----------|----------------------|
| ChromaDB cold start | 5–10 seconds (first request) |
| Warm request on CPU | 3–8 seconds |
| Warm request on GPU | 0.5–2 seconds |
| Query rewrite (1 retry) | Add 3–5 seconds |
| Query rewrite (2 retries) | Add 6–10 seconds |

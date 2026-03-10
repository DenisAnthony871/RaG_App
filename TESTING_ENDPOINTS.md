# API Testing Guide

Quick reference for testing Jio RAG API endpoints.

## Prerequisites

- Ollama must be running (`ollama serve`)
- uvicorn server must be running (`python main.py`)
- API should be accessible at `http://127.0.0.1:8000`

---

## 1. Health Check

Verify the API is running and responding.

```bash
curl http://127.0.0.1:8000/health
```

**Expected Response:**

```json
{"status": "healthy"}
```

---

## 2. Get Vector Store Stats

Check how many vectors are stored in ChromaDB.

```bash
curl http://127.0.0.1:8000/stats
```

**Expected Response:**

```json
{
  "total_vectors": 42,
  "collection": "jio_knowledge_base",
  "db_path": "./chroma_db_v4"
}
```

---

## 3. Chat - Ask a Question

Send a query to the RAG pipeline and get an answer.

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Jio Fiber?"}'
```

**Expected Response:**

```json
{
  "request_id": "a1b2c3d4",
  "answer": "Jio Fiber is a high-speed broadband service...",
  "status": "success",
  "response_time_ms": 1234.56
}
```

---

## 4. Chat - Troubleshooting Query

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I fix my Jio connection?"}'
```

---

## 5. Chat - Billing/Plan Query

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the prepaid plans available?"}'
```

---

## Common Errors & Fixes

### 404 Not Found
- ❌ Wrong endpoint path
- ✅ Use `/health`, `/stats`, or `/chat`

### 500 Internal Server Error
- ❌ Ollama not running
- ✅ Start Ollama: `ollama serve`

### Connection Refused
- ❌ API not running
- ✅ Start API: `python main.py`

### Empty Response
- ❌ Knowledge base empty
- ✅ Run the ingestion notebook: `rag.ipynb`

---

## Using PowerShell (Windows)

```powershell
# Health check
curl http://127.0.0.1:8000/health

# Chat request
$body = @{query = "What is Jio Fiber?"} | ConvertTo-Json
curl -X POST http://127.0.0.1:8000/chat `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body
```

---

## Using Python Requests

```python
import requests

BASE_URL = "http://127.0.0.1:8000"

# Health check
resp = requests.get(f"{BASE_URL}/health")
print(resp.json())

# Chat
payload = {"query": "What is Jio Fiber?"}
resp = requests.post(f"{BASE_URL}/chat", json=payload)
print(resp.json())
```

---

## Batch Testing

Save as `test_api.sh`:

```bash
#!/bin/bash

API_URL="http://127.0.0.1:8000"

echo "=== Testing Jio RAG API ==="

echo -e "\n1. Health Check"
curl $API_URL/health
echo -e "\n"

echo "2. Vector Store Stats"
curl $API_URL/stats
echo -e "\n"

echo "3. Test Query: 'What is Jio Fiber?'"
curl -X POST $API_URL/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Jio Fiber?"}'
echo -e "\n"

echo "=== Tests Complete ==="
```

Run with: `bash test_api.sh`

---

## Performance Testing

```bash
# Measure response time
time curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Jio Fiber?"}'
```

Expected: 2-5 seconds (depends on Ollama model performance)

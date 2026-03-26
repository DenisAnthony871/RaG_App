import time
import logging
import uuid
import os
import secrets
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from langchain_core.messages import HumanMessage, AIMessage
from rag_graph import graph
from database import vectorstore, check_ollama_health
from config import DB_PATH, COLLECTION_NAME
from chat_history import (
    init_db,
    create_conversation,
    conversation_exists,
    save_message,
    load_history,
    get_conversation_summary,
    delete_conversation,
)
import uvicorn


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ============= API KEY AUTH =============
API_KEY = os.getenv("JIO_RAG_API_KEY")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(request: Request, api_key: str = Security(api_key_header)):
    if not API_KEY:
        logger.error("API_KEY not set in environment — all requests will be rejected")
        raise HTTPException(status_code=500, detail="Server misconfiguration: API key not set")
    if not api_key or not secrets.compare_digest(api_key, API_KEY):
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(f"Rejected request — invalid or missing API key | IP: {client_ip}")
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    logger.info("Checking Ollama availability...")
    check_ollama_health()
    init_db()
    logger.info("API startup complete")
    yield


app = FastAPI(title="Jio RAG Support API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: lock down to frontend URL before production
    allow_methods=["POST", "GET", "DELETE"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ============= MODELS =============
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    conversation_id: Optional[str] = None

    @field_validator("query")
    @classmethod
    def strip_query(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be blank")
        return v.strip()


class ChatResponse(BaseModel):
    request_id: str
    conversation_id: str
    answer: str
    status: str = "success"
    response_time_ms: float


# ============= ENDPOINTS =============

# Public endpoint — no auth required
@app.get("/health")
def health():
    return {"status": "healthy"}


# Protected endpoints — require valid API key
@app.get("/stats", dependencies=[Security(verify_api_key)])
def stats():
    try:
        result = vectorstore.get()
        count = len(result.get("ids", []) if result else [])
        return {"total_vectors": count, "collection": COLLECTION_NAME, "db_path": DB_PATH}
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch stats")


@app.post("/chat", response_model=ChatResponse, dependencies=[Security(verify_api_key)])
def chat(request: ChatRequest):
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[{request_id}] Query: {request.query[:80]}")
    start = time.time()

    # Resolve or create conversation
    conversation_id = request.conversation_id
    if conversation_id and not conversation_exists(conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not conversation_id:
        conversation_id = create_conversation()
        logger.info(f"[{request_id}] New conversation: {conversation_id}")

    # Load history and build message list
    history = load_history(conversation_id)
    messages = []
    for msg in history:
        if msg["role"] == "human":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "ai":
            messages.append(AIMessage(content=msg["content"]))

    # Append current query
    messages.append(HumanMessage(content=request.query))

    try:
        result = graph.invoke({"messages": messages})
        answer = result["messages"][-1].content
        response_time = (time.time() - start) * 1000

        # Persist both turns
        save_message(conversation_id, "human", request.query)
        save_message(conversation_id, "ai", answer)

        logger.info(f"[{request_id}] Done in {response_time:.2f}ms")
        return ChatResponse(
            request_id=request_id,
            conversation_id=conversation_id,
            answer=answer,
            status="success",
            response_time_ms=round(response_time, 2)
        )
    except Exception as e:
        logger.error(f"[{request_id}] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process query")


@app.get("/conversations/{conversation_id}", dependencies=[Security(verify_api_key)])
def get_conversation(conversation_id: str):
    summary = get_conversation_summary(conversation_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Conversation not found")
    history = load_history(conversation_id)
    return {"conversation": summary, "messages": history}


@app.delete("/conversations/{conversation_id}", dependencies=[Security(verify_api_key)])
def remove_conversation(conversation_id: str):
    deleted = delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted", "conversation_id": conversation_id}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False, workers=1)
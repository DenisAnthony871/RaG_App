import time
import logging
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from langchain_core.messages import HumanMessage
from rag_graph import graph
from database import vectorstore, check_ollama_health
from config import DB_PATH, COLLECTION_NAME
import uvicorn


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


app = FastAPI(title="Jio RAG Support API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Check Ollama availability on startup"""
    logger.info("Checking Ollama availability...")
    check_ollama_health()
    logger.info("API startup complete")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)

    @field_validator("query")
    @classmethod
    def strip_query(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be blank")
        return v.strip()


class ChatResponse(BaseModel):
    request_id: str
    answer: str
    status: str = "success"
    response_time_ms: float


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/stats")
def stats():
    try:
        result = vectorstore.get()
        count = len(result.get("ids", []) if result else [])
        return {"total_vectors": count, "collection": COLLECTION_NAME, "db_path": DB_PATH}
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch stats")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[{request_id}] Query: {request.query[:80]}")
    start = time.time()
    try:
        result = graph.invoke({"messages": [HumanMessage(content=request.query)]})
        answer = result["messages"][-1].content
        response_time = (time.time() - start) * 1000
        logger.info(f"[{request_id}] Done in {response_time:.2f}ms")
        return ChatResponse(
            request_id=request_id,
            answer=answer,
            status="success",
            response_time_ms=round(response_time, 2)
        )
    except Exception as e:
        logger.error(f"[{request_id}] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process query")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False, workers=1)
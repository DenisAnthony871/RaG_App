import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
import uuid

# Autouse env mocking is critical before we import main so it absorbs the fake values.
@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("JIO_RAG_API_KEY", "test-api-key-12345")
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:3000")
    import importlib
    import main
    importlib.reload(main)

@pytest.fixture
def mock_graph():
    with patch("main.graph") as mock:
        mock.invoke.return_value = {
            "messages": [AIMessage(content="Mocked answer from graph")],
            "confidence": 0.9,
            "rewrite_count": 0
        }
        yield mock

@pytest.fixture
def mock_db():
    with patch("main.create_conversation", return_value=str(uuid.uuid4())) as cc, \
         patch("main.load_history", return_value=[]) as lh, \
         patch("main.save_message") as sm, \
         patch("main.log_query") as lq, \
         patch("main.delete_conversation", return_value=True) as dc, \
         patch("main.get_conversation_summary", return_value={
             "conversation_id": str(uuid.uuid4()),
             "created_at": "2026-04-06T00:00:00Z",
             "updated_at": "2026-04-06T00:00:00Z",
             "message_count": 2
         }) as gcs:
        yield {
            "create_conversation": cc,
            "load_history": lh,
            "save_message": sm,
            "log_query": lq,
            "delete_conversation": dc,
            "get_conversation_summary": gcs
        }

@pytest.fixture
def client(mock_graph, mock_db):

    # Patch database startup checks before importing FastAPI app
    with patch("database.check_ollama_health"), \
         patch("chat_history.init_db"), \
         patch("main.check_ollama_health"), \
         patch("main.init_db"), \
         patch("main.vectorstore") as vs_mock:
        
        vs_mock.get.return_value = {"ids": ["1", "2", "3"]}
        
        from main import app
        yield TestClient(app)

@pytest.fixture
def auth_headers():
    return {"X-API-Key": "test-api-key-12345"}

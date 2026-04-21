def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_chat_no_auth(client):
    response = client.post("/chat", json={"query": "test query"})
    assert response.status_code == 401

def test_chat_wrong_key(client):
    response = client.post("/chat", headers={"X-API-Key": "wrong-key"}, json={"query": "test query"})
    assert response.status_code == 401

def test_chat_valid_key(client, auth_headers):
    response = client.post("/chat", headers=auth_headers, json={"query": "What is Jio?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "conversation_id" in data
    assert "confidence" in data
    assert data["status"] == "success"

def test_chat_query_too_short(client, auth_headers):
    response = client.post("/chat", headers=auth_headers, json={"query": ""})
    assert response.status_code == 422

def test_chat_query_too_long(client, auth_headers):
    long_query = "a" * 501
    response = client.post("/chat", headers=auth_headers, json={"query": long_query})
    assert response.status_code == 422

def test_chat_no_conversation_id(client, auth_headers, mock_db):
    response = client.post("/chat", headers=auth_headers, json={"query": "testing new conv"})
    assert response.status_code == 200
    assert mock_db["create_conversation"].called

def test_chat_valid_conversation_id(client, auth_headers, mock_db):
    # get_conversation_summary returns a valid dict by default — existing conversation is found.
    response = client.post("/chat", headers=auth_headers, json={"query": "testing existing", "conversation_id": "test-id"})
    assert response.status_code == 200
    assert not mock_db["create_conversation"].called

def test_chat_unknown_conversation_id(client, auth_headers, mock_db):
    # Conversation does not exist at all — get_conversation_summary returns None
    mock_db["get_conversation_summary"].return_value = None
    response = client.post("/chat", headers=auth_headers, json={"query": "testing unknown", "conversation_id": "bad-id"})
    assert response.status_code == 404


def test_chat_cross_tenant_conversation_id(client, auth_headers, mock_db):
    # Conversation exists but is owned by a different API key.
    # get_conversation_summary returns None when owner_id doesn't match —
    # the caller must not be able to load another tenant's history.
    mock_db["get_conversation_summary"].return_value = None
    response = client.post("/chat", headers=auth_headers, json={"query": "stealing history", "conversation_id": "other-owners-id"})
    assert response.status_code == 404

def test_get_conversation_with_auth(client, auth_headers, mock_db):
    # Configure exact mock returns to ensure structural integrity and deterministic flow
    mock_db["get_conversation_summary"].return_value = {
        "conversation_id": "test-id",
        "created_at": "2026-04-06T00:00:00",
        "updated_at": "2026-04-06T00:00:00",
        "message_count": 2
    }
    mock_db["load_history"].return_value = [{"role": "human", "content": "mock content"}]
    
    response = client.get("/conversations/test-id", headers=auth_headers)
    
    # Assert side effects — owner_id is now a SHA-256 hash of the API key (not the raw secret)
    import hashlib
    expected_owner = hashlib.sha256(b"test-api-key-12345").hexdigest()
    mock_db["get_conversation_summary"].assert_called_with("test-id", owner_id=expected_owner)
    mock_db["load_history"].assert_called_with("test-id")
    
    assert response.status_code == 200
    data = response.json()
    assert "conversation" in data
    assert "messages" in data

def test_delete_conversation_with_auth(client, auth_headers, mock_db):
    mock_db["delete_conversation"].return_value = True
    response = client.delete("/conversations/test-id", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

def test_delete_conversation_not_found(client, auth_headers, mock_db):
    mock_db["delete_conversation"].return_value = False
    response = client.delete("/conversations/test-id", headers=auth_headers)
    assert response.status_code == 404

def test_get_stats_without_auth(client):
    response = client.get("/stats")
    assert response.status_code == 401

def test_get_conversation_wrong_owner(client, mock_db):
    # Simulate a different API key — get_conversation_summary returns None (not owned by this key)
    mock_db["get_conversation_summary"].return_value = None
    response = client.get("/conversations/some-id", headers={"X-API-Key": "test-api-key-12345"})
    assert response.status_code == 404

def test_delete_conversation_wrong_owner(client, mock_db):
    # Simulate a different owner — delete_conversation returns False (not owned by this key)
    mock_db["delete_conversation"].return_value = False
    response = client.delete("/conversations/some-id", headers={"X-API-Key": "test-api-key-12345"})
    assert response.status_code == 404

def test_verify_api_key_not_set(client, monkeypatch):
    monkeypatch.setattr("main.API_KEY", None)
    response = client.post("/chat", headers={"X-API-Key": "any-key"}, json={"query": "test"})
    assert response.status_code == 500

def test_chat_query_blank(client, auth_headers):
    response = client.post("/chat", headers=auth_headers, json={"query": "   "})
    assert response.status_code == 422

def test_request_size_limit_content_length(client, auth_headers):
<<<<<<< HEAD
    # Exercise the RequestSizeLimitMiddleware content-length branch by
    # sending a real large payload so httpx sets the Content-Length correctly.
    large_payload = b"a" * 3000000
=======
    response = client.post("/chat", headers={**auth_headers, "Content-Length": "10000000"}, json={"query": "test"})
    assert response.status_code == 413

def test_request_size_limit_body_stream(client, auth_headers):
    large_payload = b"a" * 10000000
>>>>>>> b40c08e4ffd3a63e1801b68deb8333adb42f56cf
    response = client.post("/chat", headers=auth_headers, content=large_payload)
    assert response.status_code == 413

def test_stats_exception(client, auth_headers):
    from unittest.mock import patch
    with patch("main.vectorstore.get", side_effect=Exception("DB Error")):
        response = client.get("/stats", headers=auth_headers)
        assert response.status_code == 500

def test_chat_graph_empty_messages(client, auth_headers, mock_graph):
    mock_graph.invoke.return_value = {"messages": []}
    response = client.post("/chat", headers=auth_headers, json={"query": "test"})
    assert response.status_code == 500

def test_chat_graph_index_error(client, auth_headers, mock_graph):
    mock_graph.invoke.side_effect = IndexError("Graph state error")
    response = client.post("/chat", headers=auth_headers, json={"query": "test"})
    assert response.status_code == 500

def test_chat_bad_request_error(client, auth_headers, mock_graph):
    from main import BadRequestError
    mock_graph.invoke.side_effect = BadRequestError("Bad request")
    response = client.post("/chat", headers=auth_headers, json={"query": "test"})
    assert response.status_code == 400

def test_chat_value_error(client, auth_headers, mock_graph):
    mock_graph.invoke.side_effect = ValueError("Internal value error")
    response = client.post("/chat", headers=auth_headers, json={"query": "test"})
    assert response.status_code == 500

def test_chat_timeout_error(client, auth_headers, mock_graph):
    mock_graph.invoke.side_effect = TimeoutError("Timeout")
    response = client.post("/chat", headers=auth_headers, json={"query": "test"})
    assert response.status_code == 504

def test_chat_unexpected_error(client, auth_headers, mock_graph):
    mock_graph.invoke.side_effect = Exception("Unexpected")
    response = client.post("/chat", headers=auth_headers, json={"query": "test"})
    assert response.status_code == 500

def test_chat_save_messages_batch_error(client, auth_headers, mock_db):
    mock_db["save_messages_batch"].side_effect = Exception("DB save error")
    response = client.post("/chat", headers=auth_headers, json={"query": "test"})
    # It logs the error but still returns 200 with the answer
    assert response.status_code == 200

def test_chat_log_query_error(client, auth_headers, mock_db):
    mock_db["log_query"].side_effect = Exception("Log error")
    response = client.post("/chat", headers=auth_headers, json={"query": "test"})
    # It logs the error but still returns 200 with the answer
    assert response.status_code == 200

def test_global_exception_handler(auth_headers):
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    from main import app
    
    # Create client with raise_server_exceptions=False to catch the 500 response
    test_client = TestClient(app, raise_server_exceptions=False)
    
    with patch("main.get_conversation_summary", side_effect=Exception("Unhandled")):
        response = test_client.get("/conversations/test-id", headers=auth_headers)
        assert response.status_code == 500

import pytest

def test_request_size_limit_normal_body(client, auth_headers):
    response = client.post("/chat", headers=auth_headers, json={"query": "normal size"})
    assert response.status_code == 200

def test_chat_httpx_read_timeout(client, auth_headers, mock_graph):
    from httpx import ReadTimeout
    mock_graph.invoke.side_effect = ReadTimeout("Timeout")
    response = client.post("/chat", headers=auth_headers, json={"query": "test"})
    assert response.status_code == 504

def test_chat_concurrent_timeout(client, auth_headers, mock_graph):
    from concurrent.futures import TimeoutError as FuturesTimeoutError
    mock_graph.invoke.side_effect = FuturesTimeoutError("Timeout")
    response = client.post("/chat", headers=auth_headers, json={"query": "test"})
    assert response.status_code == 504

def test_chat_runtime_error(client, auth_headers, mock_graph):
    mock_graph.invoke.side_effect = RuntimeError("Runtime error")
    response = client.post("/chat", headers=auth_headers, json={"query": "test"})
    assert response.status_code == 500

@pytest.mark.asyncio
async def test_global_exception_handler_direct():
    from main import global_exception_handler
    from fastapi import Request
    from unittest.mock import MagicMock
    mock_request = MagicMock(spec=Request)
    response = await global_exception_handler(mock_request, Exception("Arbitrary Exception"))
    assert response.status_code == 500
    import json
    assert json.loads(response.body) == {"detail": "Internal server error"}

@pytest.mark.asyncio
async def test_rate_limit_handler():
    from main import rate_limit_handler
    from slowapi.errors import RateLimitExceeded
    from fastapi import Request
    from unittest.mock import MagicMock
    
    mock_request = MagicMock(spec=Request)
    # Ensure request.client is not None
    mock_request.client = MagicMock()
    mock_request.client.host = "127.0.0.1"
    
    mock_limit = MagicMock()
    mock_limit.error_message = None
    response = await rate_limit_handler(mock_request, RateLimitExceeded(mock_limit))
    assert response.status_code == 429
    import json
    assert "Too many requests" in json.loads(response.body)["detail"]

@pytest.mark.asyncio
async def test_rate_limit_handler_client_none():
    from main import rate_limit_handler
    from slowapi.errors import RateLimitExceeded
    from fastapi import Request
    from unittest.mock import MagicMock
    
    mock_request = MagicMock(spec=Request)
    # Simulate internal dispatch where request.client is None
    mock_request.client = None
    
    mock_limit = MagicMock()
    mock_limit.error_message = None
    response = await rate_limit_handler(mock_request, RateLimitExceeded(mock_limit))
    assert response.status_code == 429

def test_chat_persistence_and_logging_asserted(client, auth_headers, mock_db):
    response = client.post("/chat", headers=auth_headers, json={"query": "test persistence"})
    assert response.status_code == 200
    mock_db["save_messages_batch"].assert_called_once()
    mock_db["log_query"].assert_called_once()
    
    # Verify save_messages_batch was called with the right arguments
    args, kwargs = mock_db["save_messages_batch"].call_args
    assert len(args) >= 2
    assert isinstance(args[1], list)
    assert args[1][0][0] == "human"
    assert args[1][0][1] == "test persistence"
    assert args[1][1][0] == "ai"


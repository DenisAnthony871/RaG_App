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
    response = client.post("/chat", headers=auth_headers, json={"query": "hi"})
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

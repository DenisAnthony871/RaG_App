import pytest
import chat_history
from unittest.mock import patch

@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_chat_history.db"
    with patch("chat_history.DB_FILE", str(db_file)):
        chat_history.init_db()
        yield str(db_file)

def test_create_conversation(temp_db):
    conv_id = chat_history.create_conversation(owner_id="key-a")
    assert conv_id is not None
    assert isinstance(conv_id, str)
    assert chat_history.conversation_exists(conv_id) is True

def test_conversation_exists_unknown(temp_db):
    assert chat_history.conversation_exists("unknown-id") is False

def test_save_and_load_message(temp_db):
    conv_id = chat_history.create_conversation(owner_id="key-a")
    chat_history.save_message(conv_id, "human", "hello")
    chat_history.save_message(conv_id, "ai", "hi there")
    
    history = chat_history.load_history(conv_id)
    assert len(history) == 2
    assert history[0]["role"] == "human"
    assert history[0]["content"] == "hello"
    assert history[1]["role"] == "ai"
    assert history[1]["content"] == "hi there"

def test_save_message_invalid_conv(temp_db):
    with pytest.raises(ValueError):
        chat_history.save_message("invalid", "human", "test")

def test_delete_conversation(temp_db):
    conv_id = chat_history.create_conversation(owner_id="key-a")
    assert chat_history.delete_conversation(conv_id, owner_id="key-a") is True
    assert chat_history.conversation_exists(conv_id) is False

def test_delete_conversation_wrong_owner(temp_db):
    conv_id = chat_history.create_conversation(owner_id="key-a")
    # Key B cannot delete Key A's conversation
    assert chat_history.delete_conversation(conv_id, owner_id="key-b") is False
    assert chat_history.conversation_exists(conv_id) is True

def test_delete_conversation_unknown(temp_db):
    assert chat_history.delete_conversation("unknown", owner_id="key-a") is False

def test_get_conversation_summary(temp_db):
    conv_id = chat_history.create_conversation(owner_id="key-a")
    chat_history.save_message(conv_id, "human", "q")
    chat_history.save_message(conv_id, "ai", "a")
    summary = chat_history.get_conversation_summary(conv_id, owner_id="key-a")
    assert summary["conversation_id"] == conv_id
    assert summary["message_count"] == 2

def test_get_conversation_summary_wrong_owner(temp_db):
    conv_id = chat_history.create_conversation(owner_id="key-a")
    # Key B cannot see Key A's conversation
    summary = chat_history.get_conversation_summary(conv_id, owner_id="key-b")
    assert summary is None

def test_log_query(temp_db):
    conv_id = chat_history.create_conversation(owner_id="key-a")
    chat_history.log_query(conv_id, "req1", "test query", 100.5, 0.9, 0)
    
    with chat_history.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT conversation_id, request_id, query, confidence FROM query_logs")
        logs = cursor.fetchall()
    
    assert len(logs) == 1
    assert logs[0][0] == conv_id
    assert logs[0][1] == "req1"
    assert logs[0][2] == "test query"
    assert logs[0][3] == 0.9

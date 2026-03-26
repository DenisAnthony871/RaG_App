import sqlite3
import logging
import uuid
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Absolute path derived from this file's location — avoids unexpected working directory issues
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_history.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    # Enforce foreign key constraints on every connection
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables if they don't exist"""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
            ON messages(conversation_id)
        """)
        conn.commit()
    logger.info("Chat history database initialized")


def create_conversation() -> str:
    """Create a new conversation and return its ID"""
    conversation_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO conversations (conversation_id, created_at, updated_at) VALUES (?, ?, ?)",
            (conversation_id, now, now)
        )
        conn.commit()
    return conversation_id


def conversation_exists(conversation_id: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM conversations WHERE conversation_id = ?",
            (conversation_id,)
        ).fetchone()
    return row is not None


def save_message(conversation_id: str, role: str, content: str):
    """Save a single message to the database"""
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        # Verify conversation exists before inserting to prevent orphaned rows
        row = conn.execute(
            "SELECT 1 FROM conversations WHERE conversation_id = ?",
            (conversation_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"Cannot save message — conversation '{conversation_id}' does not exist")
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (conversation_id, role, content, now)
        )
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?",
            (now, conversation_id)
        )
        conn.commit()


def load_history(conversation_id: str) -> list[dict]:
    """Load full message history for a conversation"""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT role, content, timestamp FROM messages WHERE conversation_id = ? ORDER BY id ASC",
            (conversation_id,)
        ).fetchall()
    return [{"role": row["role"], "content": row["content"], "timestamp": row["timestamp"]} for row in rows]


def get_conversation_summary(conversation_id: str) -> Optional[dict]:
    """Get conversation metadata"""
    with get_connection() as conn:
        conv = conn.execute(
            "SELECT conversation_id, created_at, updated_at FROM conversations WHERE conversation_id = ?",
            (conversation_id,)
        ).fetchone()
        if not conv:
            return None
        count = conn.execute(
            "SELECT COUNT(*) as total FROM messages WHERE conversation_id = ?",
            (conversation_id,)
        ).fetchone()
    return {
        "conversation_id": conv["conversation_id"],
        "created_at": conv["created_at"],
        "updated_at": conv["updated_at"],
        "message_count": count["total"]
    }


def delete_conversation(conversation_id: str) -> bool:
    """Delete a conversation and all its messages. Returns True if deleted."""
    with get_connection() as conn:
        # Delete messages first (CASCADE handles this if FK is ON, but explicit for clarity)
        conn.execute(
            "DELETE FROM messages WHERE conversation_id = ?",
            (conversation_id,)
        )
        # Capture rowcount from conversations DELETE — this is the correct existence check
        convo_result = conn.execute(
            "DELETE FROM conversations WHERE conversation_id = ?",
            (conversation_id,)
        )
        conn.commit()
    return convo_result.rowcount > 0
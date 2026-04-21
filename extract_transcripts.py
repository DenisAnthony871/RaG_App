import sqlite3
import os
from datetime import datetime

DB_FILE = 'chat_history.db'
OUTPUT_FILE = 'qualitative_transcripts.md'

def main():
    if not os.path.exists(DB_FILE):
        print(f"Error: {DB_FILE} not found in the current directory.")
        return

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        # Fetch conversations with at least one message
        conversations = c.execute("""
            SELECT c.conversation_id, c.created_at, c.owner_id 
            FROM conversations c
            WHERE EXISTS (SELECT 1 FROM messages m WHERE m.conversation_id = c.conversation_id)
            ORDER BY c.created_at DESC
        """).fetchall()
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("# Qualitative Chat Transcripts\n\n")
            f.write("This document contains the raw conversation logs for qualitative review and analysis.\n\n")
            
            if not conversations:
                f.write("*No conversations found in the database.*\n")
            
            for conv in conversations:
                conv_id = conv['conversation_id']
                f.write(f"## Conversation ID: `{conv_id}`\n")
                f.write(f"- **Started At:** {conv['created_at']}\n")
                f.write(f"- **Owner ID:** `{conv['owner_id']}`\n\n")
                
                messages = c.execute(
                    "SELECT role, content, timestamp FROM messages WHERE conversation_id = ? ORDER BY id ASC", 
                    (conv_id,)
                ).fetchall()
                
                for msg in messages:
                    role_emoji = "🧑 **User**" if msg['role'].lower() == 'human' else "🤖 **AI**"
                    f.write(f"{role_emoji} `[{msg['timestamp']}]`\n")
                    f.write(f"> {msg['content'].replace(chr(10), chr(10) + '> ')}\n\n")
                
                # Fetch query logs for this conversation to add confidence/timing context
                logs = c.execute(
                    "SELECT query, confidence, response_time_ms, rewrite_count FROM query_logs WHERE conversation_id = ? ORDER BY id ASC",
                    (conv_id,)
                ).fetchall()
                
                if logs:
                    f.write("### Diagnostics & Analytics\n")
                    f.write("| Query | Confidence | Response Time (ms) | Rewrites |\n")
                    f.write("| --- | --- | --- | --- |\n")
                    for log in logs:
                        safe_query = log['query'].replace('\n', ' ')[:50] + ("..." if len(log['query']) > 50 else "")
                        f.write(f"| {safe_query} | {log['confidence']} | {log['response_time_ms']} | {log['rewrite_count']} |\n")
                    f.write("\n")
                
                f.write("---\n\n")
                
        print(f"✅ Successfully exported {len(conversations)} conversations to {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"❌ Error generating transcripts: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    main()

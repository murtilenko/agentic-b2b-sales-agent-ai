import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = "data/memory_store.sqlite"

# Ensure DB exists with required table
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory (
        lead_id TEXT PRIMARY KEY,
        messages TEXT,
        turned_to_manual INTEGER DEFAULT 0,
        turned_to_manual_at TEXT,
        last_transaction_type TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()


def get_conversation(lead_id: str) -> List[Dict]:
    """Return conversation history for a lead_id."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT messages FROM memory WHERE lead_id = ?", (lead_id,))
    row = cursor.fetchone()
    conn.close()

    if row and row[0]:
        import json
        return json.loads(row[0])
    return []


def update_conversation(
    lead_id: str,
    messages: List[Dict],
    metadata: Optional[Dict] = None
) -> None:
    """Update the memory for a lead: thread + status flags."""
    metadata = metadata or {}
    turned_to_manual = int(metadata.get("turned_to_manual", 0))
    turned_to_manual_at = metadata.get("turned_to_manual_at")
    last_transaction_type = metadata.get("last_transaction_type")

    import json
    serialized = json.dumps(messages)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO memory (lead_id, messages, turned_to_manual, turned_to_manual_at, last_transaction_type)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(lead_id) DO UPDATE SET
        messages = excluded.messages,
        turned_to_manual = excluded.turned_to_manual,
        turned_to_manual_at = excluded.turned_to_manual_at,
        last_transaction_type = excluded.last_transaction_type
    """, (
        lead_id,
        serialized,
        turned_to_manual,
        turned_to_manual_at,
        last_transaction_type
    ))

    conn.commit()
    conn.close()


def mark_as_manual(lead_id: str) -> None:
    """Set turned_to_manual = True with current timestamp."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE memory
    SET turned_to_manual = 1,
        turned_to_manual_at = ?
    WHERE lead_id = ?
    """, (datetime.utcnow().isoformat(), lead_id))
    conn.commit()
    conn.close()


def get_manual_leads() -> List[str]:
    """Return all lead_ids that were handed off to manual."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT lead_id FROM memory WHERE turned_to_manual = 1")
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result

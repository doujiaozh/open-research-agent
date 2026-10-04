import sqlite3, os, json
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "./data/agent.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT,
            history TEXT,
            result TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    return conn

def save_run(goal, history, result):
    conn = init_db()
    conn.execute(
        "INSERT INTO runs (goal, history, result, created_at) VALUES (?, ?, ?, ?)",
        (goal, json.dumps(history, ensure_ascii=False),
         result, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def list_runs(limit=10):
    conn = init_db()
    rows = conn.execute(
        "SELECT id, goal, created_at FROM runs ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return rows
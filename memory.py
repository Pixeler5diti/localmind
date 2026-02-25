import sqlite3
from datetime import datetime

DB = "brain.db"

def init():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            mode TEXT,
            prompt TEXT,
            response TEXT,
            focus INTEGER,
            clarity INTEGER,
            stress INTEGER
        )
    """)
    conn.commit()
    conn.close()

def save(mode, prompt, response, focus=None, clarity=None, stress=None):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO logs (timestamp, mode, prompt, response, focus, clarity, stress) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (datetime.now().isoformat(), mode, prompt, response, focus, clarity, stress)
    )
    conn.commit()
    conn.close()

def search(keyword):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT timestamp, prompt FROM logs WHERE prompt LIKE ?", ('%'+keyword+'%',))
    results = c.fetchall()
    conn.close()
    return results

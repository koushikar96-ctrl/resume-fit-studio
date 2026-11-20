from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "resumes.db"


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            content TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_resume(title: str, resume: dict) -> int:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "INSERT INTO resumes (title, content) VALUES (?, ?)",
        (title, json.dumps(resume, ensure_ascii=False)),
    )
    conn.commit()
    resume_id = cursor.lastrowid
    conn.close()
    return resume_id


def list_resumes() -> list[dict]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, title, created_at FROM resumes ORDER BY id DESC").fetchall()
    conn.close()
    return [{"id": row[0], "title": row[1], "created_at": row[2]} for row in rows]


def get_resume(resume_id: int) -> dict | None:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT content FROM resumes WHERE id = ?", (resume_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return json.loads(row[0])

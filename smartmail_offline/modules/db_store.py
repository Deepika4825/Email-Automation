"""
SQLite-based persistent inbox storage.
Replaces session-state-only storage so emails survive page refresh.
"""
from __future__ import annotations
import sqlite3, json, os
from datetime import datetime

DB_PATH = "smartmail_offline/data/inbox.db"


def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                subject   TEXT,
                sender    TEXT,
                added_at  TEXT,
                status    TEXT DEFAULT 'Open',
                category  TEXT,
                priority  TEXT,
                sentiment TEXT,
                action    TEXT,
                summary   TEXT,
                reply     TEXT,
                score     REAL,
                data_json TEXT
            )
        """)


def add(result: dict) -> int:
    result["added_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    result["status"]   = "Open"
    pri = result.get("priority", {})
    with _conn() as con:
        cur = con.execute("""
            INSERT INTO emails
            (subject, sender, added_at, status, category, priority,
             sentiment, action, summary, reply, score, data_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            result.get("subject", ""),
            result.get("sender", ""),
            result["added_at"],
            "Open",
            result.get("category", ""),
            pri.get("priority", "low"),
            pri.get("sentiment", "NEUTRAL"),
            pri.get("action", "reply"),
            result.get("summary", ""),
            result.get("reply", ""),
            pri.get("score", 0.0),
            json.dumps(result),
        ))
        return cur.lastrowid


def get_all() -> list[dict]:
    with _conn() as con:
        rows = con.execute("SELECT * FROM emails ORDER BY id DESC").fetchall()
    return [_row_to_dict(r) for r in rows]


def get(idx: int) -> dict | None:
    with _conn() as con:
        row = con.execute("SELECT * FROM emails WHERE id=?", (idx,)).fetchone()
    return _row_to_dict(row) if row else None


def update_status(idx: int, status: str):
    with _conn() as con:
        con.execute("UPDATE emails SET status=? WHERE id=?", (status, idx))


def count() -> int:
    with _conn() as con:
        return con.execute("SELECT COUNT(*) FROM emails").fetchone()[0]


def filter_by(category=None, priority=None, status=None) -> list[dict]:
    query = "SELECT * FROM emails WHERE 1=1"
    params = []
    if category:
        query += " AND category=?"; params.append(category)
    if priority:
        query += " AND priority=?"; params.append(priority)
    if status:
        query += " AND status=?";   params.append(status)
    query += " ORDER BY id DESC"
    with _conn() as con:
        rows = con.execute(query, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def to_context_string() -> str:
    rows = get_all()
    return "\n".join(
        f"[{r['id']}] Subject:{r.get('subject','?')} | Cat:{r.get('category','?')} | "
        f"Pri:{r.get('priority',{}).get('priority','?')} | "
        f"Action:{r.get('priority',{}).get('action','?')} | "
        f"Status:{r.get('status','?')} | Summary:{r.get('summary','?')}"
        for r in rows
    )


def get_all_for_export() -> list[dict]:
    rows = get_all()
    return [{
        "ID":        r["id"],
        "Subject":   r.get("subject", ""),
        "Sender":    r.get("sender", ""),
        "Category":  r.get("category", ""),
        "Priority":  r.get("priority", {}).get("priority", ""),
        "Sentiment": r.get("priority", {}).get("sentiment", ""),
        "Action":    r.get("priority", {}).get("action", ""),
        "Status":    r.get("status", ""),
        "Summary":   r.get("summary", ""),
        "Added":     r.get("added_at", ""),
    } for r in rows]


def _row_to_dict(row) -> dict:
    d = dict(row)
    try:
        full = json.loads(d.pop("data_json", "{}"))
        full["id"]       = d["id"]
        full["status"]   = d["status"]
        full["added_at"] = d["added_at"]
        return full
    except Exception:
        return d

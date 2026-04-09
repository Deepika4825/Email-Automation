"""
Virtual inbox stored in Streamlit session state.
Supports: add, navigate, status update, filter, export.
"""
from __future__ import annotations
import streamlit as st
from datetime import datetime

STATUSES = ["Open", "In Progress", "Resolved"]


def _inbox() -> list[dict]:
    if "inbox" not in st.session_state:
        st.session_state.inbox = []
    return st.session_state.inbox


def add_email(result: dict) -> int:
    """Add a processed email result to inbox. Returns its index."""
    inbox = _inbox()
    result["status"] = "Open"
    result["added_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    result["id"] = len(inbox)
    inbox.append(result)
    return result["id"]


def get_all() -> list[dict]:
    return _inbox()


def get(idx: int) -> dict | None:
    inbox = _inbox()
    return inbox[idx] if 0 <= idx < len(inbox) else None


def update_status(idx: int, status: str):
    inbox = _inbox()
    if 0 <= idx < len(inbox):
        inbox[idx]["status"] = status


def count() -> int:
    return len(_inbox())


def filter_by(category: str = None, priority: str = None, status: str = None) -> list[dict]:
    inbox = _inbox()
    result = inbox
    if category:
        result = [e for e in result if e.get("category") == category]
    if priority:
        result = [e for e in result if e.get("priority", {}).get("priority") == priority]
    if status:
        result = [e for e in result if e.get("status") == status]
    return result


def to_context_string() -> str:
    """Flatten inbox to a string for LLM assistant queries."""
    lines = []
    for e in _inbox():
        lines.append(
            f"[{e['id']}] Subject: {e.get('subject','?')} | "
            f"Category: {e.get('category','?')} | "
            f"Priority: {e.get('priority',{}).get('priority','?')} | "
            f"Action: {e.get('priority',{}).get('action','?')} | "
            f"Status: {e.get('status','?')} | "
            f"Summary: {e.get('summary','?')}"
        )
    return "\n".join(lines)

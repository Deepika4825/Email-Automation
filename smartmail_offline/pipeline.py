"""Central AI pipeline."""
from __future__ import annotations
import re, sys, os
sys.path.insert(0, os.path.dirname(__file__))

from modules.classifier      import classify
from modules.ner_extractor   import extract
from modules.priority_engine import score
from modules.llm_engine      import summarize, generate_reply
from modules.rag_store       import add as rag_add, search as rag_search
from modules.tone_detector   import detect_tone
from modules.db_store        import init_db, add as db_add

# Init DB on import
init_db()


def clean(text: str) -> str:
    from bs4 import BeautifulSoup
    text = BeautifulSoup(text, "html.parser").get_text(separator=" ")
    text = re.sub(r"^>.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"https?://\S+", "", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def parse(raw: str) -> tuple[str, str, str]:
    subject, sender = "", ""
    m = re.search(r"Subject:\s*(.+)", raw, re.IGNORECASE)
    if m: subject = m.group(1).strip()
    m2 = re.search(r"From:\s*(.+)", raw, re.IGNORECASE)
    if m2: sender = m2.group(1).strip()
    body = re.sub(r"(Subject|From|To|Date):\s*.+\n?", "", raw).strip()
    return subject, sender, clean(body)


def run(raw: str) -> dict:
    subject, sender, body = parse(raw)
    full = f"{subject} {body}".strip()

    clf      = classify(full)
    entities = extract(full)
    priority = score(full, sender=sender)
    tone     = detect_tone(full)
    summary  = summarize(body or full)
    reply    = generate_reply(full, clf["category"], summary)
    similar  = rag_search(full)

    result = {
        "subject":    subject,
        "sender":     sender,
        "body":       body,
        "raw":        raw,
        "category":   clf["category"],
        "cat_scores": clf["scores"],
        "entities":   entities,
        "priority":   priority,
        "tone":       tone,
        "summary":    summary,
        "reply":      reply,
        "similar":    similar,
    }

    # Store in FAISS + SQLite
    rag_add(full, {
        "subject":  subject, "sender": sender,
        "category": clf["category"],
        "priority": priority["priority"],
        "action":   priority["action"],
        "summary":  summary,
    })
    result["id"] = db_add(result)
    return result


def run_bulk(texts: list[str]) -> list[dict]:
    """Process multiple emails and return results list."""
    return [run(t) for t in texts if t.strip()]

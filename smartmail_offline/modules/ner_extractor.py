"""spaCy NER + regex action items."""
from __future__ import annotations
import re

_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is None:
        import spacy
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            from spacy.cli import download
            download("en_core_web_sm")
            _nlp = spacy.load("en_core_web_sm")
    return _nlp

_ACTION_RE = re.compile(
    r"(please\s+\w+|kindly\s+\w+|you\s+need\s+to|action\s+required|"
    r"follow\s+up|send\s+us|submit|confirm|review|approve|schedule)[^.!?]*[.!?]?",
    re.IGNORECASE,
)

def extract(text: str) -> dict:
    doc = _get_nlp()(text[:5000])
    result = {"names": [], "dates": [], "organizations": [], "amounts": [], "action_items": []}
    seen = set()
    for ent in doc.ents:
        key = {"PERSON": "names", "DATE": "dates", "TIME": "dates",
               "ORG": "organizations", "MONEY": "amounts"}.get(ent.label_)
        if key and ent.text not in seen:
            result[key].append(ent.text)
            seen.add(ent.text)
    for m in _ACTION_RE.finditer(text):
        item = m.group(0).strip()
        if item and item not in result["action_items"]:
            result["action_items"].append(item)
    return result

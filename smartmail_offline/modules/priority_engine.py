"""Priority scoring: keywords + sentiment + sender importance."""
from __future__ import annotations
from config import URGENCY_KEYWORDS, VIP_TITLES

_sent = None

def _get_sent():
    global _sent
    if _sent is None:
        try:
            from transformers import pipeline
            _sent = pipeline("sentiment-analysis",
                             model="distilbert-base-uncased-finetuned-sst-2-english",
                             truncation=True, max_length=512)
        except Exception:
            _sent = "fallback"
    return _sent

def score(text: str, sender: str = "") -> dict:
    lower = text.lower()
    hits = {"high": 0, "medium": 0, "low": 0}
    matched = []
    for level, kws in URGENCY_KEYWORDS.items():
        for kw in kws:
            if kw in lower:
                hits[level] += 1
                matched.append(kw)

    vip = any(t in sender.lower() for t in VIP_TITLES)
    sentiment = "NEUTRAL"
    s = _get_sent()
    if s != "fallback":
        try:
            sentiment = s(text[:512])[0]["label"]
        except Exception:
            pass

    # Suggested action
    if "refund" in lower or "escalate" in lower or "legal" in lower:
        action = "escalate"
    elif hits["high"] > 0 or sentiment == "NEGATIVE":
        action = "reply"
    elif "unsubscribe" in lower or "newsletter" in lower:
        action = "ignore"
    else:
        action = "reply"

    if hits["high"] > 0 or sentiment == "NEGATIVE" or vip:
        priority, sc = "high", min(1.0, 0.6 + hits["high"] * 0.1 + (0.15 if vip else 0))
    elif hits["medium"] > 0:
        priority, sc = "medium", min(0.7, 0.4 + hits["medium"] * 0.1)
    else:
        priority, sc = "low", max(0.1, 0.3 - hits["low"] * 0.05)

    return {"priority": priority, "score": round(sc, 2), "sentiment": sentiment,
            "matched_keywords": matched, "sender_vip": vip, "action": action}

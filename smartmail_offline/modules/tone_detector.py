"""
Tone detection — classifies email tone beyond basic sentiment.
Uses keyword patterns (no model needed).
"""
from __future__ import annotations
import re

TONES = {
    "aggressive":  ["unacceptable", "furious", "outraged", "demand", "lawsuit",
                    "disgusting", "worst", "terrible", "horrible", "angry"],
    "urgent":      ["asap", "urgent", "immediately", "right now", "critical",
                    "emergency", "deadline", "overdue", "time sensitive"],
    "formal":      ["dear", "sincerely", "regards", "hereby", "pursuant",
                    "kindly", "respectfully", "please find attached"],
    "friendly":    ["thanks", "appreciate", "great", "wonderful", "happy",
                    "pleased", "looking forward", "hope you are well"],
    "confused":    ["not sure", "confused", "unclear", "don't understand",
                    "could you clarify", "what does", "i don't know"],
}


def detect_tone(text: str) -> dict:
    lower = text.lower()
    scores = {}
    for tone, keywords in TONES.items():
        hits = sum(1 for kw in keywords if kw in lower)
        scores[tone] = round(hits / len(keywords), 3)

    dominant = max(scores, key=scores.get)
    if scores[dominant] == 0:
        dominant = "neutral"

    return {"dominant_tone": dominant, "scores": scores}

"""Summarization + reply + AI assistant query."""
from __future__ import annotations
import re
from config import OPENAI_API_KEY

# ── Summarize ─────────────────────────────────────────────────────────────────
def summarize(text: str) -> str:
    if len(text.split()) < 40:
        return text
    return _oai("Summarize this email in 2-3 sentences. Be concise.", text) if OPENAI_API_KEY else _extractive(text)

# ── Reply ─────────────────────────────────────────────────────────────────────
_TEMPLATES = {
    "HR":        "Thank you for your message. Our HR team has received your request and will respond within 1–2 business days.",
    "spam":      "This message has been identified as spam and will not receive a reply.",
    "complaint": "We sincerely apologize for the inconvenience. Our team is reviewing your concern and will provide a resolution within 24 hours.",
    "inquiry":   "Thank you for reaching out. We have received your inquiry and will get back to you shortly.",
    "sales":     "Thank you for your interest. Our sales team will follow up with a detailed proposal soon.",
}

def generate_reply(text: str, category: str, summary: str) -> str:
    if OPENAI_API_KEY:
        prompt = f"Email category: {category}. Summary: {summary}. Write a polite professional reply in 3-4 sentences."
        return _oai(prompt, text[:800])
    return _TEMPLATES.get(category, _TEMPLATES["inquiry"])

# ── AI Assistant query ────────────────────────────────────────────────────────
def answer_query(query: str, inbox_context: str) -> str:
    if OPENAI_API_KEY:
        prompt = (f"You are an email assistant. Based on the inbox below, answer: '{query}'\n\n"
                  f"INBOX:\n{inbox_context[:3000]}")
        return _oai(prompt, "")
    return _local_query(query, inbox_context)

def _oai(system: str, user: str) -> str:
    from openai import OpenAI
    msgs = [{"role": "system", "content": system}]
    if user:
        msgs.append({"role": "user", "content": user})
    r = OpenAI(api_key=OPENAI_API_KEY).chat.completions.create(
        model="gpt-3.5-turbo", messages=msgs, max_tokens=200, temperature=0.4)
    return r.choices[0].message.content.strip()

def _extractive(text: str, max_words: int = 60) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if len(sentences) <= 2:
        return text
    stopwords = {"i","me","my","we","our","you","your","the","a","an","is","are","was",
                 "were","be","been","have","has","had","do","does","did","will","would",
                 "could","should","to","of","in","on","at","for","with","and","or","but",
                 "not","this","that","it","its","as","by","from","so","if","about"}
    words = re.findall(r"\b\w+\b", text.lower())
    freq = {}
    for w in words:
        if w not in stopwords and len(w) > 2:
            freq[w] = freq.get(w, 0) + 1
    def sc(s):
        ws = re.findall(r"\b\w+\b", s.lower())
        return sum(freq.get(w, 0) for w in ws) / max(len(ws), 1)
    ranked = sorted(enumerate(sentences), key=lambda x: sc(x[1]), reverse=True)
    sel, wc = [], 0
    for idx, s in ranked:
        w = len(s.split())
        if wc + w > max_words and sel:
            break
        sel.append((idx, s))
        wc += w
    sel.sort(key=lambda x: x[0])
    return " ".join(s for _, s in sel)

def _local_query(query: str, context: str) -> str:
    q = query.lower()
    lines = context.split("\n")
    if "urgent" in q or "high" in q:
        matches = [l for l in lines if "high" in l.lower()]
        return "High priority emails:\n" + "\n".join(matches[:5]) if matches else "No high priority emails found."
    if "complaint" in q:
        matches = [l for l in lines if "complaint" in l.lower()]
        return "Complaint emails:\n" + "\n".join(matches[:5]) if matches else "No complaint emails found."
    if "action" in q or "reply" in q:
        matches = [l for l in lines if "reply" in l.lower() or "escalate" in l.lower()]
        return "Emails needing action:\n" + "\n".join(matches[:5]) if matches else "No action items found."
    return "Try queries like: 'Show urgent emails', 'Summarize complaints', 'Which emails need action?'"

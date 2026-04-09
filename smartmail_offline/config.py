import os
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY", "")
EMAIL_CATEGORIES = ["HR", "spam", "complaint", "inquiry", "sales"]
EMBEDDING_MODEL  = "all-MiniLM-L6-v2"
FAISS_INDEX_PATH = "smartmail_offline/data/faiss.bin"
FAISS_META_PATH  = "smartmail_offline/data/faiss_meta.json"

URGENCY_KEYWORDS = {
    "high":   ["urgent", "asap", "immediately", "critical", "emergency",
               "deadline", "overdue", "escalate", "action required", "refund"],
    "medium": ["soon", "follow up", "reminder", "pending", "waiting", "please respond"],
    "low":    ["fyi", "newsletter", "update", "whenever", "no rush", "optional"],
}
VIP_TITLES = ["ceo", "director", "manager", "president", "vp", "head of", "executive"]

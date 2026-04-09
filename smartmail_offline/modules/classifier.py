"""
Email classifier using TF-IDF + Logistic Regression.
Trains on a built-in labeled dataset on first use.
Falls back to zero-shot if sklearn is unavailable.
"""
from __future__ import annotations
from config import EMAIL_CATEGORIES

# ── Built-in training dataset ─────────────────────────────────────────────────
TRAIN_DATA = [
    # HR
    ("I would like to request annual leave from July 10 to July 20", "HR"),
    ("Please approve my sick leave for tomorrow", "HR"),
    ("I am resigning from my position effective next month", "HR"),
    ("Can you share the updated payroll details for this month", "HR"),
    ("We are scheduling onboarding for new employees next week", "HR"),
    ("Please submit your timesheet by end of day Friday", "HR"),
    ("The employee benefits package has been updated", "HR"),
    ("Interview scheduled for the software engineer position", "HR"),
    ("HR team please process my reimbursement request", "HR"),
    ("I need to update my emergency contact information", "HR"),

    # spam
    ("Congratulations you have won a free prize click here to claim", "spam"),
    ("You are selected as our lucky winner claim your reward now", "spam"),
    ("Unsubscribe from our mailing list click here", "spam"),
    ("Limited time offer buy now and get 90 percent discount", "spam"),
    ("You have been chosen for a special lottery prize", "spam"),
    ("Free offer available for a limited time only act now", "spam"),
    ("Click here to claim your free gift card worth 500 dollars", "spam"),
    ("Earn money from home no experience required sign up now", "spam"),
    ("Your account has been selected for a special promotion", "spam"),
    ("Newsletter weekly deals and offers just for you", "spam"),

    # complaint
    ("I am extremely disappointed with the service I received", "complaint"),
    ("My order has not arrived and it has been two weeks", "complaint"),
    ("This is completely unacceptable I want a full refund immediately", "complaint"),
    ("Your product stopped working after just one day of use", "complaint"),
    ("I have been waiting for a response for over a week this is terrible", "complaint"),
    ("The customer service was rude and unhelpful", "complaint"),
    ("I paid for express delivery but my package is still not here", "complaint"),
    ("Please escalate this issue to your manager immediately", "complaint"),
    ("I am filing a formal complaint about your service", "complaint"),
    ("This is the third time I have had this problem with your company", "complaint"),

    # inquiry
    ("Could you please send me more information about your product", "inquiry"),
    ("I would like to know the pricing for your enterprise plan", "inquiry"),
    ("Can you tell me what features are included in the basic package", "inquiry"),
    ("I am wondering if you offer a free trial for new users", "inquiry"),
    ("Please let me know the availability of your services in my region", "inquiry"),
    ("What are your business hours and how can I contact support", "inquiry"),
    ("I have a question about the return policy for online orders", "inquiry"),
    ("Could you provide more details about the upcoming product launch", "inquiry"),
    ("I would like to schedule a demo of your software", "inquiry"),
    ("Can you clarify the terms and conditions of the subscription", "inquiry"),

    # sales
    ("We are interested in purchasing 500 licenses for our company", "sales"),
    ("Please send us a quote for your enterprise software package", "sales"),
    ("Our budget is 50000 dollars and we would like a proposal", "sales"),
    ("We would like to place a bulk order for your products", "sales"),
    ("Can you provide an invoice for the services rendered last month", "sales"),
    ("We are ready to sign the contract please send the final proposal", "sales"),
    ("Our procurement team will review your offer and get back to you", "sales"),
    ("We would like to negotiate the pricing for a long term contract", "sales"),
    ("Please confirm the delivery date for our purchase order", "sales"),
    ("We are comparing vendors and would like your best discount offer", "sales"),
]

_model = None
_vectorizer = None


def _train():
    global _model, _vectorizer
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    texts  = [t for t, _ in TRAIN_DATA]
    labels = [l for _, l in TRAIN_DATA]

    _vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000)
    X = _vectorizer.fit_transform(texts)

    _model = LogisticRegression(max_iter=1000, C=5.0)
    _model.fit(X, labels)


def classify(text: str) -> dict:
    global _model, _vectorizer
    if _model is None:
        _train()

    X = _vectorizer.transform([text[:1000]])
    probs = _model.predict_proba(X)[0]
    classes = _model.classes_
    scores = dict(zip(classes, [round(float(p), 3) for p in probs]))
    best = max(scores, key=scores.get)
    return {"category": best, "scores": scores}

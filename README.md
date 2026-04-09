SmartMail AI

An offline AI-powered Email Intelligence and Automation System built with Python and Streamlit.

Live Demo

https://email-automation-gokxe6pv2dtrb4tpxhekhc.streamlit.app/

Features

Email Classification
Classifies emails into HR, Spam, Complaint, Inquiry, and Sales using TF-IDF and Logistic Regression or machine learning models.

Named Entity Recognition
Extracts important information such as names, dates, organizations, amounts, and action items using spaCy.

Priority Engine
Determines email priority as High, Medium, or Low based on urgency keywords, sentiment analysis, and sender importance.

Tone Detection
Identifies the tone of the email such as aggressive, urgent, formal, friendly, or neutral.

AI Email Summarization
Generates short summaries of emails using NLP techniques.

Smart Reply Generator
Suggests professional email replies based on email content and category.

RAG Memory Search
Stores email embeddings in a FAISS vector database and retrieves similar past emails for reference.

Virtual Inbox Simulator
Stores multiple emails and allows tracking of their status such as Open, In Progress, and Resolved.

AI Email Assistant
Supports queries such as showing urgent emails, summarizing complaints, and identifying emails that require action.

Analytics Dashboard
Displays insights based on email categories, priority levels, and suggested actions.

Tech Stack

Python
Streamlit
spaCy
scikit-learn
FAISS
Sentence Transformers
HuggingFace Transformers
SQLite
BeautifulSoup

Run Locally

Install dependencies from requirements file
Install spaCy language model

Run the Streamlit application using app.py

Project Structure

smartmail_offline/

app.py
pipeline.py
config.py
requirements.txt

modules/

classifier.py
ner_extractor.py
priority_engine.py
tone_detector.py
llm_engine.py
rag_store.py
db_store.py

Highlights

Offline AI email intelligence system without Gmail API integration
Complete NLP and LLM pipeline
RAG-based memory search using FAISS
Real-world email automation simulation
End-to-end AI product-level project

Future Improvements

Gmail API integration for real-time email sync
Multi-language email support
Advanced phishing and spam detection
Improved LLM-based reasoning system

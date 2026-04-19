"""
Configuration settings for PE Due Diligence RAG System.
All API keys and configuration loaded from environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
CHUNKS_DIR = DATA_DIR / "chunks"
METRICS_DIR = DATA_DIR / "metrics"
INDEXES_DIR = BASE_DIR / "indexes"

# ========================
# GROQ LLM (FREE)
# ========================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL_NAME = "llama-3.3-70b-versatile"

# ========================
# EMBEDDINGS (FREE, local)
# ========================
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_BATCH_SIZE = 32

# ========================
# TWILIO WHATSAPP
# ========================
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
WHATSAPP_FROM = os.getenv("WHATSAPP_FROM", "")
WHATSAPP_WEBHOOK_URL = os.getenv("WHATSAPP_WEBHOOK_URL", "")

# ========================
# SEC EDGAR SETTINGS
# ========================
SEC_BASE_URL = "https://data.sec.gov/submissions"
SEC_ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/full-index"
SEC_USER_AGENT = "PE Due Diligence Research bot research@example.com"
SEC_RATE_LIMIT_DELAY = 0.12  # ~8 requests per second (SEC limit is 10)

# ========================
# LANGCHAIN SETTINGS
# ========================
RETRIEVAL_K = 5  # Number of documents to retrieve
MAX_CHUNK_WORDS = 300  # Max words per chunk

# ========================
# MENU OPTIONS
# ========================
MENU_OPTIONS = {
    "1": {
        "name": "Risk Discovery",
        "description": "Analyze Risk Factors section",
        "index": "risk_factors",
        "section": "Risk Factors"
    },
    "2": {
        "name": "Business Quality",
        "description": "EBITDA, margins, revenue analysis",
        "index": "md&a",
        "section": "MD&A"
    },
    "3": {
        "name": "Valuation Assumptions",
        "description": "Growth rates, LBO model inputs",
        "index": "md&a",
        "section": "MD&A"
    },
    "4": {
        "name": "Value Creation",
        "description": "Margin improvement opportunities",
        "index": "business",
        "section": "Business"
    },
    "5": {
        "name": "Due Diligence Validation",
        "description": "Verify management claims vs actuals",
        "index": "risk_factors",
        "section": "Risk Factors"
    }
}

# ========================
# SEC SECTION MAPPING
# ========================
SEC_SECTIONS = {
    "1": "Business",
    "1A": "Risk Factors",
    "1B": "Unresolved Staff Comments",
    "2": "Properties",
    "3": "Legal Proceedings",
    "4": "Mine Safety Disclosures",
    "5": "Market for Registrant's Securities",
    "6": "Selected Financial Data",
    "7": "MD&A",
    "7A": "Quantitative Disclosures",
    "8": "Financial Statements",
    "9": "Changes in Accountants",
    "9A": "Controls and Procedures",
    "10": "Directors and Executives",
    "11": "Executive Compensation",
    "12": "Security Ownership",
    "13": "Related Party Transactions",
    "14": "Principal Accountant Fees"
}

# Sections to index (priority order)
PRIORITY_SECTIONS = ["1A", "7", "1", "8", "7A"]

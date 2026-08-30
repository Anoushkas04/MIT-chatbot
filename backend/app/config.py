import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BACKEND_DIR = Path(__file__).resolve().parent.parent

# Docs directory: check env var, then minor_project_docs, then data, then fallback
_default_docs = (
    BACKEND_DIR.parent / "minor_project_docs"
    if (BACKEND_DIR.parent / "minor_project_docs").exists()
    else (BACKEND_DIR.parent / "data" if (BACKEND_DIR.parent / "data").exists() else BACKEND_DIR / "data")
)
DOCS_DIR = Path(os.environ.get("DOCS_DIR", str(_default_docs)))
DATA_DIR = Path(os.environ.get("DATA_DIR", str(BACKEND_DIR / "data")))

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", os.environ.get("CHAT_MODEL", "gemini-flash-latest"))
CHAT_MODEL = GEMINI_MODEL
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "gemini-embedding-001")

TOP_K = int(os.environ.get("TOP_K", "5"))
HIGH_CONFIDENCE_THRESHOLD = float(os.environ.get("HIGH_CONFIDENCE_THRESHOLD", "0.65"))
MAX_HISTORY_TURNS = int(os.environ.get("MAX_HISTORY_TURNS", "6"))


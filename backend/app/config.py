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

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "auto").strip().lower()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
LLM_TIMEOUT_SECONDS = float(os.environ.get("LLM_TIMEOUT_SECONDS", "90"))

VISUAL_RAG_ENABLED = os.environ.get("VISUAL_RAG_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
COLVISION_MODEL = os.environ.get("COLVISION_MODEL", "vidore/colSmol-500M")
COLVISION_DEVICE = os.environ.get("COLVISION_DEVICE", "auto").strip().lower()
COLVISION_LOCAL_FILES_ONLY = os.environ.get("COLVISION_LOCAL_FILES_ONLY", "false").strip().lower() in {"1", "true", "yes", "on"}
VISUAL_RAG_SCOPE = os.environ.get("VISUAL_RAG_SCOPE", "scanned").strip().lower()
if VISUAL_RAG_SCOPE not in {"scanned", "all"}:
    raise ValueError("VISUAL_RAG_SCOPE must be 'scanned' or 'all'.")
RAG_TOP_K_VISUAL = int(os.environ.get("RAG_TOP_K_VISUAL", "8"))
RAG_TOP_K_TEXT = int(os.environ.get("RAG_TOP_K_TEXT", "12"))
RAG_FINAL_K = int(os.environ.get("RAG_FINAL_K", "4"))
RAG_RENDER_DPI = int(os.environ.get("RAG_RENDER_DPI", "144"))

TOP_K = int(os.environ.get("TOP_K", "5"))
HIGH_CONFIDENCE_THRESHOLD = float(os.environ.get("HIGH_CONFIDENCE_THRESHOLD", "0.65"))
MAX_HISTORY_TURNS = int(os.environ.get("MAX_HISTORY_TURNS", "6"))

# Supabase Auth Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# Configurable Allowed Email Domains (comma-separated, default: learner.manipal.edu,manipal.edu)
_domains_raw = os.environ.get("ALLOWED_EMAIL_DOMAINS", "learner.manipal.edu,manipal.edu")
ALLOWED_EMAIL_DOMAINS = [d.strip().lower() for d in _domains_raw.split(",") if d.strip()]


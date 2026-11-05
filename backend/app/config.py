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
# Optional separate key for embeddings only (its own Google project, so its own free-tier
# quota); answers, translation and moderation keep GEMINI_API_KEY.
GEMINI_EMBEDDING_API_KEY = os.environ.get("GEMINI_EMBEDDING_API_KEY", "").strip() or GEMINI_API_KEY
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", os.environ.get("CHAT_MODEL", "gemini-flash-lite-latest"))
CHAT_MODEL = GEMINI_MODEL
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "gemini-embedding-001")
GEMINI_EMBEDDINGS_ENABLED = os.environ.get("GEMINI_EMBEDDINGS_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}

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

LOCAL_OCR_ENABLED = os.environ.get("LOCAL_OCR_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}
OCR_MIN_CONFIDENCE = float(os.environ.get("OCR_MIN_CONFIDENCE", "0.45"))
OCR_MAX_IMAGE_EDGE = int(os.environ.get("OCR_MAX_IMAGE_EDGE", "2600"))
OCR_CACHE_DIR = Path(os.environ.get("OCR_CACHE_DIR", str(DATA_DIR / "ocr_cache")))

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

# Database: Postgres URL (e.g. Supabase pooler) in production, local SQLite file when unset
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

# Signed session tokens (HS256), valid until the user signs out. Without a fixed secret, a
# random one is generated per process, so tokens stop working when the server restarts —
# always set it when deployed.
SESSION_SECRET = os.environ.get("SESSION_SECRET", "").strip()

# Local-only testing: when Supabase isn't configured, return the generated OTP in the
# API response so it can be entered without an email provider. Ignored if Supabase is set.
AUTH_DEV_MODE = os.environ.get("AUTH_DEV_MODE", "").strip().lower() in ("1", "true", "yes")

# The official MITra admins, fixed in code: no other account can ever be an admin, and
# the ADMIN_EMAILS environment variable is ignored. Change this list (and redeploy) to
# add or remove an admin. Names are what the audit log shows.
ADMIN_ACCOUNTS = {
    "anoushkas154@gmail.com": "Anoushka",
    "tejasrasoju@gmail.com": "Tejas",
    "186.dev.tated@gmail.com": "Dev",
}
ADMIN_EMAILS = frozenset(ADMIN_ACCOUNTS)  # exempt from the student email-domain rule

# Opt-in demo content for the Community feed (labelled samples, no fake accounts).
SEED_DEMO_COMMUNITY = os.environ.get("SEED_DEMO_COMMUNITY", "").strip().lower() in ("1", "true", "yes")


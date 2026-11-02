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

# Supabase Auth Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# Configurable Allowed Email Domains (comma-separated, default: learner.manipal.edu,manipal.edu)
_domains_raw = os.environ.get("ALLOWED_EMAIL_DOMAINS", "learner.manipal.edu,manipal.edu")
ALLOWED_EMAIL_DOMAINS = [d.strip().lower() for d in _domains_raw.split(",") if d.strip()]

# Database: Postgres URL (e.g. Supabase pooler) in production, local SQLite file when unset
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

# Signed session tokens (HS256). Without a fixed secret, a random one is generated per
# process, so tokens stop working when the server restarts — always set it when deployed.
SESSION_SECRET = os.environ.get("SESSION_SECRET", "").strip()
SESSION_TTL_DAYS = int(os.environ.get("SESSION_TTL_DAYS", "7"))

# Local-only testing: when Supabase isn't configured, return the generated OTP in the
# API response so it can be entered without an email provider. Ignored if Supabase is set.
AUTH_DEV_MODE = os.environ.get("AUTH_DEV_MODE", "").strip().lower() in ("1", "true", "yes")


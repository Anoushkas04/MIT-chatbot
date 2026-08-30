# MIT CampusOS — Backend

FastAPI backend for the MAHE MIT CampusOS platform (`../frontend`): RAG-grounded
AI copilot, Learner-ID/OTP student authentication, student community, faculty/
admin/rewards/notifications APIs, all backed by SQLite.

## Setup

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env   # then fill in the variables below
```

### Required / optional environment variables (`backend/.env`)

| Variable | Required | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Google Gemini key ([aistudio.google.com/apikey](https://aistudio.google.com/apikey)) for chat generation and embeddings. |
| `GEMINI_MODEL` / `CHAT_MODEL` | No | Overrides the chat model (default `gemini-flash-latest`). |
| `EMBEDDING_MODEL` | No | Overrides the embedding model (default `gemini-embedding-001`). |
| `TOP_K`, `HIGH_CONFIDENCE_THRESHOLD`, `MAX_HISTORY_TURNS` | No | RAG/chat tuning knobs, see `app/config.py`. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | No | Real OTP email delivery. See **Authentication** below for the fallback when these are unset. |

Never commit real values for any of the above — `.env` is gitignored; only
`.env.example` (with empty values) is tracked.

## Build the knowledge base

Run this once, and again any time files are added to `../minor_project_docs`:

```
python -m app.rag.ingest
```

This reads every PDF/CSV in `minor_project_docs`, chunks and embeds the text via
Gemini, and writes `data/chunks.json` + `data/embeddings.npy`. If the Gemini
embedding quota is exhausted (free tier is 1000 requests/day) it falls back to
a local deterministic hash embedding so the app keeps working — retrieval
quality is noticeably lower in that mode; re-run ingest once quota resets.

## Run

```
uvicorn app.main:app --reload --port 8000
```

The database (`campus_os.db`, SQLite) is created and seeded automatically on
startup (19 official departments, sample academic-calendar events, knowledge
document metadata — no fake users or posts). `GET /api/health` for a liveness
check; interactive API docs at `http://localhost:8000/docs`.

### Routers

| Prefix | Router | Covers |
|---|---|---|
| `/api/auth` | `auth_router.py` | Learner-ID/OTP signup, login, profile |
| `/api/chat` | `chat_router.py` | RAG copilot chat, source citations |
| `/api/academic` | `academic_router.py` | Academic calendar, timeline, cutoff ranks |
| `/api/faculty` | `faculty_router.py` | Faculty & cabin directory |
| `/api/posts` | `community_router.py` | Student community posts, votes, comments |
| `/api/notifications` | `notifications_router.py` | Notification center, popups |
| `/api/feedback` | `feedback_router.py` | Crowdsourced feedback / learning signals |
| `/api/admin` | `admin_router.py` | Admin console (analytics, users, moderation, events) |
| `/api/rewards` | `rewards_router.py` | Student reputation, badges, leaderboard |
| `/api/search` | `search_router.py` | Global multi-domain search |

## Authentication: Learner ID → institutional email → OTP

A student's **Learner ID is their institutional email address** — the format
is enforced by `LEARNER_ID_PATTERN` in `app/routers/auth_router.py`:
`<name><optional-digit>.mitmpl<admission-year>@learner.manipal.edu`
(e.g. `student.mitmpl2023@learner.manipal.edu`). There's no separate lookup —
the ID the student types *is* the address the OTP is sent to.

Flow: `POST /api/auth/verify-learner-id` (validates format, generates a 6-digit
OTP, hashes it before storing, sets a 10-minute expiry and 60-second resend
cooldown) → `POST /api/auth/verify-otp` (checks hash/expiry/single-use, max 5
attempts) → `POST /api/auth/register-complete` (9-digit registration number +
password + terms acceptance creates the account) → `POST /api/auth/login`
(password-based for returning users; OTP is only required once, at signup).

**Development vs. production OTP delivery** (`app/email_service.py`):

- **Development** (no `SMTP_*` vars set): the OTP is printed to the backend
  console/log instead of emailed, so signup works without any email
  provider. Look for a block starting `[DEV MODE — SMTP NOT CONFIGURED]` in
  the terminal running `uvicorn`.
- **Production** (`SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD` set):
  the OTP is emailed for real via SMTP and is never printed or logged.

## Self-check

```
python test_rag.py
```

## Notes / known limitations

- Vector store is a plain numpy cosine-similarity search over the whole corpus,
  persisted to disk — no FAISS/Pinecone service. Fine at this corpus size;
  revisit only if the knowledge base grows into the tens of thousands of chunks.
- Cutoff-rank PDFs are tabular; `pypdf` text extraction is naive and may mangle
  columns. Swap `rag/loaders.py`'s PDF path for `pdfplumber` if retrieval quality
  on those specific documents turns out to matter.
- Conversation history and auth session tokens are in-memory and reset when
  the server restarts (`app/session_memory.py`, `TOKENS_STORE` in
  `auth_router.py`).
- Password hashing (`hash_password` in `auth_router.py`) uses unsalted
  SHA-256, consistent with this codebase's existing conventions — swap for
  `bcrypt`/`argon2` before any real production deployment.
- Windows note: `app/main.py`, `app/rag/ingest.py`, and `app/seed.py` force
  UTF-8 stdout/stderr on startup, since Windows' default console codepage
  can't encode the emoji used throughout this codebase's log/print output and
  would otherwise crash with `UnicodeEncodeError`.

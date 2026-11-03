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
| `SUPABASE_URL`, `SUPABASE_ANON_KEY` | For real email | Supabase Auth sends and verifies OTP codes. See **Authentication** below. |
| `SESSION_SECRET` | Yes (deployed) | Signs login tokens; without it, logins end on every restart. |
| `DATABASE_URL` | For deployment | Postgres URL (Supabase). Empty = local SQLite `campus_os.db`. |
| `AUTH_DEV_MODE` | No | `true` returns the OTP in the API response when Supabase is unset (local testing). |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | No | Direct SMTP OTP delivery when Supabase isn't used. |

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

## Authentication: Learner ID → email OTP (no passwords)

A student's **Learner ID is their institutional email address**
(e.g. `student.mitmpl2023@learner.manipal.edu`); the OTP is sent there.

**Register** (`AuthPage`): `POST /api/auth/register-send-otp` with name +
registration number + Learner ID (validates the reg-no format and that its
admission year matches the Learner ID, rejects already-registered details, emails
a 6-digit code) → `POST /api/auth/register-verify-otp` with the code → account is
created and a session token returned.

**Sign in**: `POST /api/auth/login-send-otp` with the registration number *or*
Learner ID (code goes to the stored Learner ID) → `POST /api/auth/login-verify-otp`.

Rules (all in `app/routers/auth_router.py`, `_issue_otp` / `_verify_otp`): codes
expire after 10 minutes, are single-use, allow 5 wrong attempts, and can be
re-sent after 45 seconds. Session tokens are signed JWTs (`SESSION_SECRET`,
no expiry: a session lasts until the user signs out, which revokes it server-side), so logins survive restarts and serverless deploys.

The older password-based endpoints used by `AuthModal` (`verify-learner-id`,
`verify-otp`, `register-complete`, `login`) still work and share the same OTP checks.

### Who sends and checks the codes

| Setup | Behaviour |
|---|---|
| `SUPABASE_URL` + `SUPABASE_ANON_KEY` set | Supabase Auth generates, emails and verifies the code. |
| Supabase unset, `SMTP_*` set | Backend generates the code and emails it over SMTP. |
| Neither set | Code is printed to the uvicorn console. With `AUTH_DEV_MODE=true` it is also returned as `test_otp`, which the sign-in page displays. Local testing only. |

### One-time Supabase + Gmail setup (free, no domain needed)

1. **Gmail**: turn on 2-Step Verification, then create an App Password
   (Google Account → Security → App passwords).
2. **Supabase** → create a free project, then under **Authentication**:
   - **Emails → SMTP Settings**: enable custom SMTP. Host `smtp.gmail.com`, port
     `465`, username = your Gmail address, password = the App Password, sender
     email = the same Gmail address. Set "Minimum interval between emails" to
     45 seconds or less (the sign-in page allows a resend after 45s).
   - **Emails → Templates**: in both **Magic Link** and **Confirm signup**, put
     the code in the body, e.g. `Your MIT CampusOS code is {{ .Token }}`.
     Without `{{ .Token }}` students get a link instead of a code.
   - **Providers → Email**: email OTP length 6, expiry 600 seconds.
   - **Rate limits**: raise "emails sent per hour" (the default is low).
3. Copy **Project URL** and **anon key** (Project Settings → API) into
   `SUPABASE_URL` / `SUPABASE_ANON_KEY`, and set `SESSION_SECRET`.
4. For deployment (e.g. Vercel), set `DATABASE_URL` to the Supabase Postgres
   pooler connection string so accounts persist; tables are created on startup.

University mail servers can flag Gmail senders, so check spam/quarantine on the
first test. **Switching to Resend later** (once you own a domain): verify the
domain in Resend, then change only the Supabase SMTP settings to host
`smtp.resend.com`, port `465`, username `resend`, password = Resend API key,
sender `noreply@yourdomain`. No code changes.

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
- Chat conversation history is in-memory and resets when the server restarts
  (`app/session_memory.py`). Login sessions are signed tokens and are not affected.
- Password hashing (`hash_password` in `auth_router.py`) uses unsalted
  SHA-256, consistent with this codebase's existing conventions — swap for
  `bcrypt`/`argon2` before any real production deployment.
- Windows note: `app/main.py`, `app/rag/ingest.py`, and `app/seed.py` force
  UTF-8 stdout/stderr on startup, since Windows' default console codepage
  can't encode the emoji used throughout this codebase's log/print output and
  would otherwise crash with `UnicodeEncodeError`.

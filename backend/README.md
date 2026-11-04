# MITra — Backend

FastAPI backend for MITra (`../frontend`): a RAG-grounded campus chatbot, email-code
(OTP) sign-in for students and admins, the student Community, safety (reports,
suspensions, pleas, appeals) and the admin console. SQLite locally, Postgres when
`DATABASE_URL` is set.

How the chatbot retrieves and answers is documented in [CHATBOT.md](CHATBOT.md).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then fill in the variables below
```

### Environment variables (`backend/.env`)

| Variable | Required | Purpose |
|---|---|---|
| `SESSION_SECRET` | Yes | Signs sign-in tokens. Without it, everyone is signed out on every restart. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | For real email | Sends sign-in codes (e.g. Gmail + App Password). **Without SMTP or Supabase, codes are only printed in the backend console and nobody receives an email.** |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY` | Alternative to SMTP | Supabase Auth sends and checks the codes instead. |
| `LLM_PROVIDER` + one of `GEMINI_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | For AI answers | `auto` picks OpenAI → Anthropic → Gemini → local. With no key, answers are extractive quotes from the documents. |
| `GEMINI_EMBEDDINGS_ENABLED` | No | `true` embeds with Gemini (needs a key); otherwise a local hash embedder is used. Rebuild the index after switching. |
| `LOCAL_OCR_ENABLED` | No | On by default: reads scanned PDFs (calendars, regulations) with offline OCR. |
| `VISUAL_RAG_ENABLED` | No | Off by default: visual page search (needs `sentence-transformers[image]`, `peft`). |
| `DATABASE_URL` | For deployment | Postgres URL (e.g. Supabase pooler). Empty = local SQLite `campus_os.db`. |
| `CORS_ORIGINS` | For deployment | Browser origins allowed to call the API. Default `http://localhost:3000`. |
| `AUTH_DEV_MODE` | No | Local testing only: returns the code in the API response when no email is set up. |
| `SEED_DEMO_COMMUNITY` | No | `1` adds 6 labelled sample questions with answers to the Community feed, once, alongside real posts. |

Admins are fixed in `app/config.py` (`ADMIN_ACCOUNTS`); there is no admin setting in `.env`.
Never commit `.env`: it is gitignored, and only `.env.example` is tracked.

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

On first start the database tables are created and, if there is no chatbot index yet,
one is built from `../minor_project_docs` in the background. API docs are at
`http://localhost:8000/docs`; `GET /api/health` is the liveness check.

To rebuild the index from the command line instead: `python -m app.rag.ingest`.

### Routers

| Prefix | Router | Used by |
|---|---|---|
| `/api/auth` | `auth_router.py` | Student sign-up/sign-in, admin sign-in, sign-out, disabled-account appeals |
| `/api/chat` | `chat_router.py` | Chatbot |
| `/api/search`, `/api/documents` | `library_router.py` | Search page: document search, list and download |
| `/api/community` | `community_v2.py` | Community feed, replies, votes |
| `/api/users` | `users_router.py` | Network: people search, reporting |
| `/api/me` | `me_router.py` | Notifications, suspension status, pleas |
| `/api/admin/community`, `/api/admin/audit` | `admin_community.py` | Admin Community moderation, audit log |
| `/api/admin/reports`, `suspensions`, `pleas`, `appeals` | `admin_safety.py` | Admin safety |
| `/api/admin/dataset` | `admin_dataset.py` | Admin dataset manager |
| `/api/admin/monitoring`, `insights`, `accounts` | `admin_insights.py` | Admin overview pages |
| `/api/admin/users/toggle-status` | `admin_router.py` | Disable / re-enable an account; also the shared admin check |

### Dataset changes

Adding, replacing or removing a document in the admin Dataset page saves the change at
once, then rebuilds the whole index **in the background** (the chunking is page-aware, so
there is no cheap single-file update). The page shows progress and the new chunk counts
when the build finishes. A change made while a build is running queues one more build,
so the index always ends up matching the documents. Removed and replaced files are kept
in `data/doc_history/`.

## Authentication: email codes, no passwords

A student's **Learner ID is their institutional email** (e.g.
`student.mitmpl2023@learner.manipal.edu`); codes are sent there.

- **Register:** `POST /api/auth/register-send-otp` (name, registration number, Learner ID)
  → `POST /api/auth/register-verify-otp` with the code.
- **Sign in:** `POST /api/auth/login-send-otp` with the registration number or Learner ID
  → `POST /api/auth/login-verify-otp`.
- **Admins:** `POST /api/auth/admin-send-otp` / `admin-verify-otp`, only for the emails in
  `ADMIN_ACCOUNTS`. Admin and student sessions are separate and don't affect each other.

Codes are 6 digits, expire after 10 minutes, are single-use and can be re-sent after
45 seconds. Five wrong codes lock sign-in for 30 minutes. Sessions don't time out: they
last until the person signs out, which ends every session for that account.

### One-time Supabase + Gmail setup (optional)

1. **Gmail:** turn on 2-Step Verification, then create an App Password.
2. **Supabase** → new project → **Authentication**:
   - **Emails → SMTP Settings:** host `smtp.gmail.com`, port `465`, your Gmail address
     and App Password. Set the minimum interval between emails to 45 seconds or less.
   - **Emails → Templates:** put `{{ .Token }}` in **Magic Link** and **Confirm signup**,
     or students get a link instead of a code.
   - **Providers → Email:** OTP length 6, expiry 600 seconds.
3. Copy the Project URL and anon key into `SUPABASE_URL` / `SUPABASE_ANON_KEY`.

University mail servers can flag Gmail senders, so check spam on the first test.

## Tests

```bash
python -m pytest tests -q
```

Covers the chatbot API contract, citations, retrieval and providers without calling any
paid API. The L2 corpus tests in `tests/test_chatbot_l2.py` run against the built index
(`data/`) and are skipped if there is none or OCR is off. `test_supabase_auth.py` is a manual
sign-in smoke test against a running server.

## Notes

- Chat history used for follow-up questions is kept in memory and resets on restart
  (`app/session_memory.py`); sign-in sessions are not affected.
- Windows: `app/main.py`, `app/rag/ingest.py` and `app/seed.py` force UTF-8 console
  output, since the default codepage can't print the emoji in log lines.

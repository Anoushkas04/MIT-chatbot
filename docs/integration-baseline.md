# Next frontend integration baseline

Branch: `integration/next-frontend`

This document records the starting state used for the staged migration. It is
not a claim that every existing feature is production-ready.

## Repository layout during migration

- `backend/`: existing FastAPI, SQLite, RAG, and domain APIs.
- `frontend/`: existing Vite client retained as the functional reference.
- `frontend-next/`: redesigned Next.js client under staged integration.
- `minor_project_docs/`: source corpus used by the RAG ingestion job.

## Baseline checks before integration

| Area | Result |
| --- | --- |
| Existing Vite production build | Passed; emitted a bundle-size warning. |
| Existing Vite lint | Completed with approximately 45 warnings. |
| Backend Python compilation | Passed. |
| Backend RAG self-check | Failed because a long sentence exceeded the configured chunk size. |
| Redesigned frontend typecheck | Passed before import. |
| Redesigned frontend production build | Blocked on vulnerable Next.js 16.4.0/Turbopack behavior. |
| Redesigned frontend dependency audit | Reported critical and high advisories before repair. |

## Required local configuration

Backend values are documented in `backend/.env.example`. The integrated
frontend only requires:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Authentication is explicitly excluded from this migration batch. The Next.js
client uses guest mode and must not manufacture an account, identity, or token.

## Batch-one acceptance criteria

1. The existing Vite client remains unchanged and runnable.
2. `frontend-next` installs from its committed pnpm lockfile.
3. Lint, TypeScript, and production build checks pass.
4. No critical or high production dependency advisories remain.
5. Guest mode is clearly identified and does not collect credentials.
6. The backend health indicator fails gracefully when FastAPI is unavailable.


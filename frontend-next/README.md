# MITra Next.js frontend

This directory contains the in-progress integration of the redesigned MITra
interface with the existing CampusOS FastAPI backend. The original Vite client
remains in `../frontend` until feature parity is reviewed and approved.

## Current batch

- Redesigned Next.js interface imported without replacing the Vite client.
- Patched dependency graph, strict TypeScript build, and ESLint checks.
- Shared typed API client with timeouts, read retries, structured errors, and
  optional bearer-token support.
- Public backend health and department clients.
- Honest guest workspace; no fake login or authentication state.

AI chat, RAG, search, calendar, community, and role-workspace integration are
deliberately outside this first batch.

## Setup

```powershell
Copy-Item .env.example .env.local
pnpm install --frozen-lockfile
pnpm dev
```

The frontend runs at `http://localhost:3000`. The backend URL defaults to
`http://localhost:8000` and can be changed with
`NEXT_PUBLIC_API_BASE_URL` in `.env.local`.

## Checks

```powershell
pnpm lint
pnpm typecheck
pnpm build
pnpm audit --prod
```


# FinFlow — Backend

FastAPI-based REST API for **FinFlow**: subscriptions, transactions, categories, budgets, payments, exchange rates, and dashboard aggregates. Uses async SQLAlchemy, Alembic migrations, and **[Supabase Auth](https://supabase.com/docs/guides/auth)** JWT verification (ES256 via JWKS; optional legacy HS256).

## Stack

| Layer | Choice |
|--------|--------|
| Runtime | Python 3.x |
| Framework | FastAPI |
| Database | PostgreSQL (async via `asyncpg`; Supabase-compatible) |
| Migrations | Alembic |
| Auth | Supabase access JWT (`Authorization: Bearer …`), local user row synced from `sub` + `email` |

## Repository layout (Clean Architecture)

```
app/
├── api/v1/           # HTTP routes, Pydantic schemas
├── application/      # Services (use cases)
├── domain/           # Entities, repository protocols, exceptions
├── infrastructure/   # SQLAlchemy models & repositories, DB session
├── core/             # Security, logging, exception handlers
└── main.py           # ASGI app factory
alembic/              # Migrations
```

## Prerequisites

- Python 3.11+ recommended  
- PostgreSQL (local or [Supabase](https://supabase.com/) with **transaction pooler** on port `6543` when using pooler mode)

## Setup

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set DATABASE_URL, SUPABASE_URL, optional SUPABASE_JWT_LEGACY_HS256_SECRET, CORS_ORIGINS
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **Health check:** `GET http://localhost:8000/health`  
- **API base:** `/api/v1` — send `Authorization: Bearer` plus the **Supabase session `access_token`** on protected routes (e.g. `/api/v1/auth/me`, `/api/v1/dashboard`)

## Vercel (`vercel.json` + root `main.py`)

This repo ships **`vercel.json`** (legacy `@vercel/python` build) and a **root** `main.py` that only does `from app.main import app`, so the real app stays in `app/main.py`. In Vercel, set the project **Root Directory** to **`backend`**, add the same keys as `.env.example` under **Environment Variables**, then deploy. Run `alembic upgrade head` once against production (not inside the serverless bundle). For local work, keep using `uvicorn app.main:app`.

## Environment variables

Copy `.env.example` to `.env`. Important keys:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://...` async URL |
| `DATABASE_USE_POOLER` | `true` when using Supabase PgBouncer (transaction mode) |
| `SUPABASE_URL` | `https://&lt;project-ref&gt;.supabase.co` — used for JWKS (`…/auth/v1/.well-known/jwks.json`) and default JWT issuer |
| `SUPABASE_JWT_LEGACY_HS256_SECRET` | Optional: legacy symmetric secret if tokens are still HS256 during JWT key rotation |
| `SUPABASE_JWT_ISSUER` / `SUPABASE_JWT_AUDIENCE` | Optional overrides for JWT `iss` / `aud` validation |
| `CORS_ORIGINS` | Comma-separated allowed origins for browser/mobile clients |

Never commit `.env`.

## Database migrations

```bash
alembic revision --autogenerate -m "describe_change"
alembic upgrade head
```

## Related repositories

| Repo | URL |
|------|-----|
| **FinFlow — Main Repo** (submodules umbrella) | https://github.com/ChamathDilshanC/FinFlow---Main-Repo |
| **FinFlow — Frontend** | https://github.com/ChamathDilshanC/FinFlow---Frontend |

Clone the full tree: `git clone --recurse-submodules https://github.com/ChamathDilshanC/FinFlow---Main-Repo.git`

## Contributing & attribution

**Human maintainer:** [ChamathDilshanC](https://github.com/ChamathDilshanC).  

Automated assistants and IDE tools (including **Cursor** / “Cursor Agent”) may be used during development; they are **not** listed as project contributors. Contributions are accepted only according to maintainer policy.

## License

Specify your license in this repo when you publish (e.g. MIT). Until then, all rights reserved by the maintainer unless stated otherwise.

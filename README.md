# FinFlow — Backend

FastAPI-based REST API for **FinFlow**: subscriptions, transactions, categories, budgets, payments, exchange rates, and dashboard aggregates. Uses async SQLAlchemy, Alembic migrations, and JWT authentication.

## Stack

| Layer | Choice |
|--------|--------|
| Runtime | Python 3.x |
| Framework | FastAPI |
| Database | PostgreSQL (async via `asyncpg`; Supabase-compatible) |
| Migrations | Alembic |
| Auth | JWT (HS256), password hashing with `bcrypt` |

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
# Edit .env — set DATABASE_URL, JWT_SECRET, CORS_ORIGINS, etc.
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **Health check:** `GET http://localhost:8000/health`  
- **API base:** `/api/v1` (e.g. `/api/v1/auth/register`, `/api/v1/dashboard`)

## Environment variables

Copy `.env.example` to `.env`. Important keys:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://...` async URL |
| `DATABASE_USE_POOLER` | `true` when using Supabase PgBouncer (transaction mode) |
| `JWT_SECRET` | Strong secret for signing tokens |
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

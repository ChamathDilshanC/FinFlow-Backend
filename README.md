# FinFlow Backend API

Production-ready backend service for the FinFlow mobile app. This API handles authentication, transactions, subscriptions, budgets, categories, and dashboard analytics.

## Technology Stack

| Area | Technologies (Name + Icon) |
|---|---|
| Backend Core | ![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white) ![Pydantic](https://img.shields.io/badge/Pydantic-E92063?logo=pydantic&logoColor=white) |
| Data Layer | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?logo=postgresql&logoColor=white) ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?logo=sqlalchemy&logoColor=white) ![asyncpg](https://img.shields.io/badge/asyncpg-0B7285?logo=postgresql&logoColor=white) |
| Migrations & Auth | ![Alembic](https://img.shields.io/badge/Alembic-4B5563?logo=databricks&logoColor=white) ![Supabase Auth](https://img.shields.io/badge/Supabase%20Auth-3ECF8E?logo=supabase&logoColor=white) ![JWT](https://img.shields.io/badge/JWT-000000?logo=jsonwebtokens&logoColor=white) |
| Platform Integration | ![Git](https://img.shields.io/badge/Git-F05032?logo=git&logoColor=white) ![Main Repo](https://img.shields.io/badge/Main%20Repo-181717?logo=github&logoColor=white) ![Frontend](https://img.shields.io/badge/Frontend-61DAFB?logo=react&logoColor=black) |

## Architecture

```text
app/
|-- api/v1/            # Route handlers and schemas
|-- application/       # Use-case services
|-- domain/            # Entities and contracts
|-- infrastructure/    # DB models/repositories/session
|-- core/              # Security/logging/exceptions
`-- main.py            # FastAPI app entry point
alembic/               # Database migrations
```

## Local Setup

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Important Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Async PostgreSQL connection string |
| `DATABASE_USE_POOLER` | Enable pooler mode when using Supabase PgBouncer |
| `SUPABASE_URL` | Used for issuer and JWKS token validation |
| `SUPABASE_JWT_LEGACY_HS256_SECRET` | Optional legacy HS256 support |
| `SUPABASE_JWT_ISSUER` / `SUPABASE_JWT_AUDIENCE` | Optional token validation overrides |
| `CORS_ORIGINS` | Comma-separated allowed origins |

## API Run & Health

- Base URL: `http://localhost:8000`
- API prefix: `/api/v1`
- Health endpoint: `GET /health`
- Protected routes require `Authorization: Bearer <access_token>`

## Related Repositories

- Main: [FinFlow - Main Repo](https://github.com/ChamathDilshanC/FinFlow---Main-Repo)
- Frontend: [FinFlow - Frontend](https://github.com/ChamathDilshanC/FinFlow---Frontend)

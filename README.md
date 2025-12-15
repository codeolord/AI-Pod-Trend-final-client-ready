# AI POD Trend Dashboard (Client Ready)

This repository is a **client-ready** POD trend ingestion + AI scoring dashboard:

- **FastAPI** backend (JWT auth, trend ingestion, AI scoring)
- **Celery** worker for async ingestion/scoring
- **Postgres** for persistence
- **Redis** for Celery + realtime events
- **Next.js** frontend dashboard (login + realtime ingestion updates)

## Quickstart (Docker)

### 1) Configure environment
Create your backend env file:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```env
ENV=development

# Docker-compose service names
DATABASE_URL=postgresql+asyncpg://pod:pod@postgres:5432/pod_db
REDIS_URL=redis://redis:6379/0

# Optional (enables AI scoring)
OPENAI_API_KEY=sk-...
```

> If `OPENAI_API_KEY` is not set, ingestion still works but AI scoring will be marked **failed** with an explicit error.

### 2) Run the stack
```bash
cd infra
docker compose up --build
```

Open:
- Frontend UI: http://localhost:3000
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### 3) First-time login
On the UI, create an account (email + password) and log in.

Then click **Run trend ingestion**.

## Testing (Smoke test)

A one-command smoke test is included. It will:
- start the stack
- wait for backend health
- register + login
- trigger ingestion
- verify trend items are returned

```bash
chmod +x scripts/test_stack.sh
./scripts/test_stack.sh
```

## API Overview

### Auth
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me` (requires `Authorization: Bearer <token>`)

### Trends (protected)
- `POST /api/v1/trends/ingest` (queues background ingestion job)
- `GET /api/v1/trends/items` (returns ingested items sorted by AI score)

### Realtime (WebSocket)
- `GET /ws/trends`

The backend publishes ingestion events to Redis and streams them via WebSocket:
- `ingest_started`
- `ingest_completed`

The UI uses these events to update status and refresh automatically.

## Branding / White-labeling

The frontend reads these env vars at build time:

- `NEXT_PUBLIC_BRAND_NAME`
- `NEXT_PUBLIC_BRAND_TAGLINE`

In Docker Compose, set these as build args in `infra/docker-compose.yml` if you want per-client branding.

Example (local):
```bash
NEXT_PUBLIC_BRAND_NAME="Acme Trends" NEXT_PUBLIC_BRAND_TAGLINE="Acme POD Intelligence" \
docker compose up --build
```

## Production Deployment

This repo supports deploying **backend + worker** as separate services and using managed Postgres/Redis.

### Railway (preferred)
Railway is the fastest path: deploy 2 services (API + Worker) plus Postgres & Redis plugins.

**Steps**
1. Create a new Railway project
2. Add **Postgres** and **Redis** plugins
3. Create 2 services from this repo:
   - **API service**
     - Root directory: `backend`
     - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Worker service**
     - Root directory: `backend`
     - Start command: `celery -A app.core.celery_app:celery_app worker -l INFO`
4. Set environment variables for both services:
   - `ENV=production`
   - `DATABASE_URL=<railway postgres url>`
   - `REDIS_URL=<railway redis url>`
   - `JWT_SECRET=<strong random string>`
   - `OPENAI_API_KEY=<optional>`
5. Deploy frontend (Railway or Vercel):
   - `NEXT_PUBLIC_API_URL=<your api https url>`
   - `NEXT_PUBLIC_BRAND_NAME=<client name>`

**Important**
- Set `JWT_SECRET` to a strong secret in production.

### Fly.io
Deploy the backend and worker as separate Fly apps, and use managed Postgres + Redis.

Suggested approach:
- `fly launch` in `backend/` (creates API app)
- Create another Fly app for worker using same image + different command
- Configure secrets:
  - `fly secrets set DATABASE_URL=... REDIS_URL=... JWT_SECRET=... OPENAI_API_KEY=...`
- Create Postgres via `fly postgres create` (or external provider)
- Use Upstash or Fly Redis for Redis

## Troubleshooting

### Postgres connection errors
Docker Compose uses Postgres healthchecks and `depends_on: condition: service_healthy` so the backend should not start before Postgres is ready.

If needed:
```bash
docker compose logs postgres
docker compose logs backend
```

### Frontend loads but shows nothing
The frontend requires `NEXT_PUBLIC_API_URL` at **build time**. Docker Compose injects it as a build arg.

Check:
```bash
docker compose logs frontend
```

### AI score missing / failed
AI scoring requires `OPENAI_API_KEY`. If absent or rate-limited, the item will show:
- `AI failed` (with error tooltip), or
- `AI pending` (if future enhancement queues scoring separately)

The system is still usable without AI scoring.

---

## Security notes for client delivery
- Change `JWT_SECRET` in production.
- Restrict CORS (`allow_origins`) to the deployed frontend domain.
- Add rate limiting (recommended for public exposure).

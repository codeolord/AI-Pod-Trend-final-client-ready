# Railway Deployment

Deploy as 3 components:
1) Backend API (FastAPI)
2) Worker (Celery)
3) Frontend (Next.js) — Railway or Vercel

## Backend API service
- Root directory: `backend`
- Build: Dockerfile detected
- Start command:
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Worker service
- Root directory: `backend`
- Build: Dockerfile detected
- Start command:
  `celery -A app.core.celery_app:celery_app worker -l INFO`

## Add plugins
- Postgres
- Redis

## Environment variables (API + Worker)
- `ENV=production`
- `DATABASE_URL=<postgres connection string>`
- `REDIS_URL=<redis connection string>`
- `JWT_SECRET=<strong random secret>`
- `OPENAI_API_KEY=<optional>`

## Frontend
Deploy `frontend/`:
- Set `NEXT_PUBLIC_API_URL=https://<your-api-domain>`
- Optional:
  - `NEXT_PUBLIC_BRAND_NAME=<Client Name>`
  - `NEXT_PUBLIC_BRAND_TAGLINE=<Client tagline>`

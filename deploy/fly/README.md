# Fly.io Deployment

Recommended: deploy API and Worker as separate Fly apps, using the same backend Docker image.

## 1) API app
From `backend/`:
```bash
fly launch
```

Set secrets:
```bash
fly secrets set ENV=production JWT_SECRET=... DATABASE_URL=... REDIS_URL=... OPENAI_API_KEY=...
```

## 2) Worker app
Create a second Fly app that uses the same backend image but runs Celery:
```bash
fly apps create <your-worker-app>
fly deploy --app <your-worker-app> --config fly.worker.toml
```

## 3) Datastores
- Postgres: `fly postgres create` (or any managed provider)
- Redis: Fly Redis (if available in your region) or Upstash

## Frontend
Deploy `frontend/` to Fly or Vercel.
Set:
- `NEXT_PUBLIC_API_URL=https://<your-api-domain>`

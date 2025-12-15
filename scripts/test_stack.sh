#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_DIR="$ROOT_DIR/infra"

EMAIL="${TEST_EMAIL:-demo@example.com}"
PASSWORD="${TEST_PASSWORD:-DemoPassw0rd!}"

echo "[1/6] Starting stack (docker compose up -d --build)"
cd "$COMPOSE_DIR"
docker compose up -d --build

echo "[2/6] Waiting for backend health..."
HEALTH_URL="http://localhost:8000/health"
deadline=$((SECONDS + 240))
until curl -fsS "$HEALTH_URL" >/dev/null 2>&1; do
  if [ $SECONDS -gt $deadline ]; then
    echo "ERROR: backend did not become healthy in time"
    docker compose logs --no-color --tail=250 backend || true
    exit 1
  fi
  sleep 5
done
echo "Backend healthy ✅"

echo "[3/6] Registering test user (safe if already exists)..."
curl -fsS -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{"email":"$EMAIL","password":"$PASSWORD"}" >/dev/null 2>&1 || true

echo "[4/6] Logging in..."
TOKEN="$(curl -fsS -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{"email":"$EMAIL","password":"$PASSWORD"}" | python -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')"
if [ -z "$TOKEN" ]; then
  echo "ERROR: could not obtain access token"
  exit 1
fi
echo "Auth ok ✅"

echo "[5/6] Triggering ingestion..."
curl -fsS -X POST "http://localhost:8000/api/v1/trends/ingest" \
  -H "Authorization: Bearer $TOKEN" >/dev/null

echo "Waiting for items to appear..."
FOUND=0
deadline=$((SECONDS + 180))
while [ $SECONDS -lt $deadline ]; do
  COUNT="$(curl -fsS "http://localhost:8000/api/v1/trends/items" -H "Authorization: Bearer $TOKEN" | python -c 'import sys, json; print(len(json.load(sys.stdin)))')"
  if [ "$COUNT" -ge 1 ]; then
    FOUND=1
    break
  fi
  sleep 5
done

if [ "$FOUND" -ne 1 ]; then
  echo "ERROR: No items found after ingestion wait window"
  echo "Worker logs:"
  docker compose logs --no-color --tail=250 worker || true
  echo "Backend logs:"
  docker compose logs --no-color --tail=250 backend || true
  exit 1
fi

echo "[6/6] Smoke test complete ✅"
echo "Open UI: http://localhost:3000"

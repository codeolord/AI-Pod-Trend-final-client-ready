from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings
import redis.asyncio as redis

router = APIRouter()

CHANNEL = "trend_events"


@router.websocket("/ws/trends")
async def ws_trends(websocket: WebSocket):
    await websocket.accept()
    r = redis.from_url(settings.redis_url, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe(CHANNEL)
    try:
        async for message in pubsub.listen():
            if message is None:
                continue
            if message.get("type") != "message":
                continue
            data = message.get("data")
            # Ensure JSON
            try:
                payload: Any = json.loads(data) if isinstance(data, str) else data
                await websocket.send_text(json.dumps(payload))
            except Exception:
                await websocket.send_text(json.dumps({"type": "raw", "data": str(data)}))
    except WebSocketDisconnect:
        pass
    finally:
        try:
            await pubsub.unsubscribe(CHANNEL)
        except Exception:
            pass
        try:
            await pubsub.close()
        except Exception:
            pass
        try:
            await r.close()
        except Exception:
            pass

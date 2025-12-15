from __future__ import annotations

import json
from typing import List

import asyncio

from app.core.celery_app import celery_app
from app.core.config import settings
from app.crud.trend_item import set_ai_fields, set_ai_failure, upsert_trend_item
from app.db.session import AsyncSessionLocal
from app.services.ai import score_trend_item_with_ai

import redis

CHANNEL = "trend_events"

def publish_event(event: dict):
    try:
        r = redis.from_url(settings.redis_url, decode_responses=True)
        r.publish(CHANNEL, json.dumps(event, default=str))
        r.close()
    except Exception:
        pass

from app.services.ingest import fetch_rss, normalize_feed_items


@celery_app.task(name="ingest_rss", bind=True)
def ingest_rss_task(self, *, urls: List[str], max_items_per_feed: int = 25, run_ai: bool = True) -> dict:
    """Celery entrypoint.

    Celery tasks are sync functions; we spin up a small asyncio loop inside.
    """

    return asyncio.run(_ingest_rss_async(urls=urls, max_items_per_feed=max_items_per_feed, run_ai=run_ai))


async def _ingest_rss_async(*, urls: List[str], max_items_per_feed: int, run_ai: bool) -> dict:
    publish_event({"type":"ingest_started","feeds":len(urls)})
    created = 0
    updated = 0
    scored = 0
    errors: list[str] = []

    async with AsyncSessionLocal() as db:
        for url in urls:
            try:
                parsed = await fetch_rss(url)
                items = normalize_feed_items(parsed, source_url=url)
                for item in items[:max_items_per_feed]:
                    orm = await upsert_trend_item(
                        db,
                        source=item["source"],
                        source_url=item.get("source_url"),
                        title=item["title"],
                        url=item["url"],
                        summary=item.get("summary"),
                        published_at=item.get("published_at"),
                        raw_json=item.get("raw_json"),
                    )
                    if orm.id:
                        # If already existed, SQLAlchemy keeps same id; we count later after commit.
                        pass

                    # Score only if needed
                    if run_ai and settings.openai_api_key and orm.ai_score_0_100 is None:
                        try:
                            out = await score_trend_item_with_ai(
                                title=orm.title,
                                summary=orm.summary or "",
                                source=orm.source,
                                url=orm.url,
                            )
                            await set_ai_fields(
                                db,
                                orm,
                                score_0_100=out.score_0_100,
                                niche=out.niche,
                                ai_json=json.dumps(out.__dict__, default=str),
                            )
                            scored += 1
                        except Exception as e:  # noqa: BLE001
                            await set_ai_failure(db, orm, error=str(e))
                            errors.append(f"AI score failed for {orm.url}: {e}")

                    created += 1

            except Exception as e:  # noqa: BLE001
                errors.append(f"Fetch failed for {url}: {e}")

        await db.commit()

    publish_event({"type":"ingest_completed","created":created,"updated":updated,"scored":scored,"errors":errors[:5]})
    return {"created": created, "updated": updated, "scored": scored, "errors": errors[:20]}

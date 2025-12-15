from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import TrendItem


async def upsert_trend_item(
    db: AsyncSession,
    *,
    source: str,
    source_url: Optional[str],
    title: str,
    url: str,
    summary: Optional[str],
    published_at: Optional[datetime],
    raw_json: Optional[str],
) -> TrendItem:
    stmt = select(TrendItem).where(TrendItem.url == url)
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()
    if existing:
        existing.source = source
        existing.source_url = source_url
        existing.title = title
        existing.summary = summary
        existing.published_at = published_at
        if raw_json:
            existing.raw_json = raw_json
        await db.flush()
        return existing

    item = TrendItem(
        source=source,
        source_url=source_url,
        title=title,
        url=url,
        summary=summary,
        published_at=published_at,
        raw_json=raw_json,
    )
    db.add(item)
    await db.flush()
    return item


async def set_ai_fields(
    db: AsyncSession,
    item: TrendItem,
    *,
    score_0_100: int,
    niche: str,
    ai_json: str,
) -> TrendItem:
    item.ai_score_0_100 = score_0_100
    item.ai_niche = niche
    item.ai_json = ai_json
    item.ai_status = "scored"
    item.ai_error = None
    await db.flush()
    return item


async def set_ai_failure(db: AsyncSession, item: TrendItem, *, error: str) -> TrendItem:
    item.ai_status = "failed"
    item.ai_error = error[:1000]
    await db.flush()
    return item

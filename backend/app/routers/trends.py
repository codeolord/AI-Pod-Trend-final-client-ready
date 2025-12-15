from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user

from app.core.config import settings
from app.db.models import TrendItem
from app.db.session import get_session
from app.schemas.trend_item import IngestRequest, IngestResponse, TrendItemOut
from app.tasks.ingest import ingest_rss_task

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/items", response_model=List[TrendItemOut])
async def list_trend_items(
    limit: int = 50,
    min_score: Optional[int] = None,
    source: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
):
    stmt = select(TrendItem).order_by(TrendItem.ai_score_0_100.desc().nullslast(), TrendItem.published_at.desc().nullslast()).limit(limit)
    if min_score is not None:
        stmt = stmt.where(TrendItem.ai_score_0_100 >= min_score)
    if source:
        stmt = stmt.where(TrendItem.source.ilike(f"%{source}%"))
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/items/{item_id}", response_model=TrendItemOut)
async def get_trend_item(item_id: int, db: AsyncSession = Depends(get_session)):
    res = await db.execute(select(TrendItem).where(TrendItem.id == item_id))
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Trend item not found")
    return item


@router.post("/ingest", response_model=IngestResponse)
async def ingest_trends(req: IngestRequest):
    urls = req.urls or settings.trend_rss_urls
    if not urls:
        raise HTTPException(status_code=400, detail="No RSS URLs configured")

    # enqueue Celery task
    task = ingest_rss_task.delay(urls=urls, max_items_per_feed=req.max_items_per_feed, run_ai=req.run_ai)
    return IngestResponse(task_id=task.id)

from typing import List, Optional

from fastapi import APIRouter, Depends

from app.core.auth import get_current_user, Depends
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MarketplaceProduct, ProductSnapshot, TrendScore
from app.db.session import get_session

router = APIRouter(dependencies=[Depends(get_current_user)])


class ProductSnapshotRead(BaseModel):
    captured_at: str
    price: float
    currency: str
    rank: int | None = None
    review_count: int | None = None
    rating: float | None = None
    estimated_sales: float | None = None

    class Config:
        from_attributes = True


class TrendScoreRead(BaseModel):
    overall_score: float
    demand_score: float
    competition_score: float
    momentum_score: float | None = None
    cluster_label: str | None = None
    niche: str | None = None

    class Config:
        from_attributes = True


class ProductRead(BaseModel):
    id: int
    marketplace: str
    external_id: str
    url: str
    title: str
    description: str | None = None
    image_url: str | None = None
    tags: str | None = None
    niche: str | None = None

    latest_snapshot: ProductSnapshotRead | None = None
    latest_trend: TrendScoreRead | None = None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ProductRead])
async def list_products(
    limit: int = 20,
    marketplace: Optional[str] = None,
    min_score: float = 0.0,
    db: AsyncSession = Depends(get_session),
):
    stmt = select(MarketplaceProduct).limit(limit)
    if marketplace:
        stmt = stmt.filter(MarketplaceProduct.marketplace == marketplace)

    res = await db.execute(stmt)
    products = res.scalars().all()

    items: List[ProductRead] = []
    for p in products:
        snap_stmt = (
            select(ProductSnapshot)
            .filter(ProductSnapshot.product_id == p.id)
            .order_by(desc(ProductSnapshot.captured_at))
            .limit(1)
        )
        trend_stmt = (
            select(TrendScore)
            .filter(TrendScore.product_id == p.id, TrendScore.overall_score >= min_score)
            .order_by(desc(TrendScore.created_at))
            .limit(1)
        )
        snap_res = await db.execute(snap_stmt)
        trend_res = await db.execute(trend_stmt)
        snap = snap_res.scalar_one_or_none()
        trend = trend_res.scalar_one_or_none()

        items.append(
            ProductRead(
                id=p.id,
                marketplace=p.marketplace,
                external_id=p.external_id,
                url=p.url,
                title=p.title,
                description=p.description,
                image_url=p.image_url,
                tags=p.tags,
                niche=p.niche,
                latest_snapshot=ProductSnapshotRead.model_validate(snap) if snap else None,
                latest_trend=TrendScoreRead.model_validate(trend) if trend else None,
            )
        )

    return items

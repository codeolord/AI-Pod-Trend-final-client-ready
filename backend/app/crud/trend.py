from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Trend as TrendORM
from app.schemas import TrendCreate


async def create_trend(db: AsyncSession, obj_in: TrendCreate) -> TrendORM:
    db_obj = TrendORM(
        marketplace=obj_in.marketplace,
        product_title=obj_in.product_title,
        niche=obj_in.niche,
        score=obj_in.score,
        demand_level=obj_in.demand_level,
        competition_level=obj_in.competition_level,
        price=obj_in.price,
        currency=obj_in.currency,
        sample_image_url=obj_in.sample_image_url,
        last_seen=obj_in.last_seen,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

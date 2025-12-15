from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TrendBase(BaseModel):
    marketplace: str
    product_title: str
    niche: str
    score: float
    demand_level: str
    competition_level: str
    price: float
    currency: str = "USD"
    sample_image_url: Optional[str] = None
    last_seen: datetime


class TrendCreate(TrendBase):
    pass


class TrendRead(TrendBase):
    id: int

    class Config:
        from_attributes = True

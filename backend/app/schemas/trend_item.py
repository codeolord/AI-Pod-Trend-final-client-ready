from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TrendItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    source_url: Optional[str] = None
    title: str
    url: str
    summary: Optional[str] = None
    published_at: Optional[datetime] = None

    ai_score_0_100: Optional[int] = Field(default=None, ge=0, le=100)
    ai_niche: Optional[str] = None
    ai_status: Optional[str] = None
    ai_error: Optional[str] = None


class IngestRequest(BaseModel):
    urls: Optional[list[str]] = None
    max_items_per_feed: int = Field(default=25, ge=1, le=200)
    run_ai: bool = True


class IngestResponse(BaseModel):
    task_id: str

from datetime import datetime
from typing import Tuple

from app.schemas import TrendCreate
from app.scrapers.base import RawListing


def _derive_levels(score: float) -> Tuple[str, str]:
    if score >= 0.8:
        return "high", "medium"
    if score >= 0.6:
        return "medium", "medium"
    return "low", "low"


def score_listing(listing: RawListing) -> TrendCreate:
    base = 0.5
    title = listing.title.lower()
    if "retro" in title or "vintage" in title:
        base += 0.1
    if "cat" in title or "dog" in title:
        base += 0.1
    if "custom" in title or "personalized" in title:
        base += 0.05

    score = max(0.0, min(1.0, base))
    demand_level, competition_level = _derive_levels(score)

    return TrendCreate(
        marketplace=listing.marketplace,
        product_title=listing.title,
        niche="auto-detected (stub)",
        score=score,
        demand_level=demand_level,
        competition_level=competition_level,
        price=listing.price,
        currency=listing.currency,
        sample_image_url=listing.image_url,
        last_seen=datetime.utcnow(),
    )

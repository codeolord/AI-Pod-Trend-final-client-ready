from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Dict, Optional


@dataclass
class RawListing:
    marketplace: str
    product_id: str
    url: str
    title: str
    price: float
    currency: str
    image_url: Optional[str] = None
    extra: Dict[str, str] | None = None


class BaseScraper(ABC):
    marketplace: str

    @abstractmethod
    async def search_trending(self, query: str, *, limit: int = 50) -> AsyncIterator[RawListing]:
        raise NotImplementedError

from __future__ import annotations

from typing import AsyncIterator

from .base import BaseScraper, RawListing


class EtsyScraper(BaseScraper):
    marketplace = "Etsy"

    async def search_trending(self, query: str, *, limit: int = 50) -> AsyncIterator[RawListing]:
        """Stub implementation returning demo listings."""
        items = [
            RawListing(
                marketplace=self.marketplace,
                product_id="ETSY-MIN-LINE",
                url="https://etsy.example/minimalist-line-art",
                title="Custom Minimalist Line Art Couple Poster",
                price=24.0,
                currency="USD",
                image_url="https://placehold.co/400x400?text=Line+Art",
            ),
            RawListing(
                marketplace=self.marketplace,
                product_id="ETSY-PET-PORTRAIT",
                url="https://etsy.example/pet-portrait",
                title="Personalized Watercolor Pet Portrait Canvas",
                price=39.0,
                currency="USD",
                image_url="https://placehold.co/400x400?text=Pet+Portrait",
            ),
        ]
        for item in items[:limit]:
            yield item

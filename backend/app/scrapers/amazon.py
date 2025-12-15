from __future__ import annotations

from typing import AsyncIterator

from .base import BaseScraper, RawListing


class AmazonScraper(BaseScraper):
    marketplace = "Amazon"

    async def search_trending(self, query: str, *, limit: int = 50) -> AsyncIterator[RawListing]:
        """Stub implementation returning demo listings.

        Replace this with real Playwright logic to scrape Amazon.
        """
        items = [
            RawListing(
                marketplace=self.marketplace,
                product_id="AMZ-RETRO-CAT",
                url="https://amazon.example/retro-cat",
                title="Vintage Retro Cat Lover T-Shirt",
                price=19.99,
                currency="USD",
                image_url="https://placehold.co/400x400?text=Retro+Cat",
            ),
            RawListing(
                marketplace=self.marketplace,
                product_id="AMZ-CUSTOM-DAD",
                url="https://amazon.example/custom-dad",
                title="Custom Best Dad Ever Mug",
                price=14.99,
                currency="USD",
                image_url="https://placehold.co/400x400?text=Dad+Mug",
            ),
        ]
        for item in items[:limit]:
            yield item

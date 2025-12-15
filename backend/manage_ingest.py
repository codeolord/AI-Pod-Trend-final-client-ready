import asyncio
from datetime import datetime

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.models import MarketplaceProduct, ProductSnapshot
from app.scrapers import AmazonScraper, EtsyScraper
from app.services import score_listing
from app.crud import create_trend


async def ingest_keyword(keyword: str, limit: int = 10) -> int:
    async with AsyncSessionLocal() as session:
        scrapers = [AmazonScraper(), EtsyScraper()]
        created = 0

        for scraper in scrapers:
            async for listing in scraper.search_trending(keyword, limit=limit):
                # Store or update product (simplified)
                prod_stmt = select(MarketplaceProduct).filter(
                    MarketplaceProduct.marketplace == listing.marketplace,
                    MarketplaceProduct.external_id == listing.product_id,
                )
                res = await session.execute(prod_stmt)
                product = res.scalar_one_or_none()
                if not product:
                    product = MarketplaceProduct(
                        marketplace=listing.marketplace,
                        external_id=listing.product_id,
                        url=listing.url,
                        title=listing.title,
                        image_url=listing.image_url,
                    )
                    session.add(product)
                    await session.flush()

                snapshot = ProductSnapshot(
                    product_id=product.id,
                    captured_at=datetime.utcnow(),
                    price=listing.price,
                    currency=listing.currency,
                    rank=None,
                    review_count=None,
                    rating=None,
                    estimated_sales=None,
                )
                session.add(snapshot)

                trend_in = score_listing(listing)
                await create_trend(session, trend_in)
                created += 1

        await session.commit()
        return created


async def _run():
    created = await ingest_keyword("t-shirt", limit=10)
    print(f"Ingested {created} demo trends into the database.")


if __name__ == "__main__":
    asyncio.run(_run())

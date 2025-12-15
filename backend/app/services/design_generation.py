from dataclasses import dataclass
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DesignAsset, MarketplaceProduct


@dataclass
class DesignRequest:
    prompt: str
    negative_prompt: Optional[str] = None
    steps: int = 30
    guidance_scale: float = 7.5


async def generate_design_for_product(
    db: AsyncSession,
    product: MarketplaceProduct,
    req: DesignRequest,
    *,
    sd_api_base: str,
    sd_api_key: Optional[str] = None,
) -> DesignAsset:
    payload = {
        "prompt": req.prompt,
        "negative_prompt": req.negative_prompt or "",
        "steps": req.steps,
        "guidance_scale": req.guidance_scale,
    }
    headers = {}
    if sd_api_key:
        headers["Authorization"] = f"Bearer {sd_api_key}"

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{sd_api_base}/txt2img", json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()

    image_url = data.get("image_url") or "https://placehold.co/800x800?text=AI+Design"
    thumb = data.get("thumbnail_url") or image_url

    asset = DesignAsset(
        product_id=product.id,
        prompt=req.prompt,
        negative_prompt=req.negative_prompt,
        provider="stable-diffusion",
        image_url=image_url,
        thumbnail_url=thumb,
        status="ready",
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset

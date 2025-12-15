from typing import Optional

from fastapi import APIRouter, Depends

from app.core.auth import get_current_user, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DesignAsset, MarketplaceProduct
from app.db.session import get_session
from app.services.design_generation import DesignRequest, generate_design_for_product

router = APIRouter(dependencies=[Depends(get_current_user)])


class DesignCreateRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None


class DesignRead(BaseModel):
    id: int
    product_id: int
    prompt: str
    negative_prompt: Optional[str]
    provider: str
    image_url: Optional[str]
    thumbnail_url: Optional[str]
    status: str

    class Config:
        from_attributes = True


@router.post("/{product_id}", response_model=DesignRead)
async def create_design_for_product(
    product_id: int,
    body: DesignCreateRequest,
    db: AsyncSession = Depends(get_session),
):
    product_res = await db.execute(select(MarketplaceProduct).filter(MarketplaceProduct.id == product_id))
    product = product_res.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    sd_api_base = "https://your-stable-diffusion-api.example.com"
    asset = await generate_design_for_product(
        db,
        product,
        DesignRequest(prompt=body.prompt, negative_prompt=body.negative_prompt),
        sd_api_base=sd_api_base,
    )
    return DesignRead.model_validate(asset)


@router.get("/{product_id}/latest", response_model=DesignRead | None)
async def get_latest_design_for_product(
    product_id: int,
    db: AsyncSession = Depends(get_session),
):
    res = await db.execute(
        select(DesignAsset)
        .filter(DesignAsset.product_id == product_id)
        .order_by(DesignAsset.created_at.desc())
        .limit(1)
    )
    asset = res.scalar_one_or_none()
    if not asset:
        return None
    return DesignRead.model_validate(asset)

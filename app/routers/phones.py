from fastapi import APIRouter, Depends
from app.db import SessionLocal
from app.models import PhoneBrand, PhoneModel
from sqlalchemy.future import select
from sqlalchemy import distinct
from sqlalchemy.ext.asyncio import AsyncSession



router = APIRouter()


async def get_db():
    async with SessionLocal() as sl:
        yield sl


@router.get("/brands")
async def get_phone_brands(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PhoneBrand).join(PhoneModel, PhoneBrand.id == PhoneModel.brand_id).where(PhoneModel.mask_available == True).distinct()
    )
    brands = result.scalars().all()
    return [{"id": brand.id, "name": brand.name} for brand in brands]

@router.get("/brands/{brand_id}/models")
async def get_phone_models(brand_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PhoneModel).where((PhoneModel.brand_id == brand_id) & (PhoneModel.mask_available == True)))
    models = result.scalars().all()
    return [{"id": model.id, "name": model.name} for model in models]
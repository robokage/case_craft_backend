from fastapi import APIRouter, Depends
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import SessionLocal
from app.models import PhoneModel

router = APIRouter()

async def get_db():
    async with SessionLocal() as sl:
        yield sl


@router.post("/prompt-only")
async def generate_with_just_prompt(prompt: str, phone_model_id:int , db:AsyncSession = Depends(get_db)):
    result = await db.execute(select(PhoneModel).where(PhoneModel.id == phone_model_id))
    phone_mdl_parm = result.scalar_one()
    model_height = phone_mdl_parm.phone_height
    model_width = phone_mdl_parm.phone_width
    model_img_path = phone_mdl_parm.s3_path
    print(f"model_height :{model_height}, model_width:{model_width}, \n model_img_path:{model_img_path} \n prompt: {prompt}")
    

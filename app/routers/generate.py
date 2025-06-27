import asyncio
import os
import zipfile
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import SessionLocal
from app.models import PhoneModel
from huggingface_hub import InferenceClient

from scripts.utils import Utils


router = APIRouter()
utils = Utils()


async def get_db():
    async with SessionLocal() as sl:
        yield sl


@router.post("/prompt-only")
async def generate_with_just_prompt(prompt: str, phone_model_id:int , db:AsyncSession = Depends(get_db)):
    result = await db.execute(select(PhoneModel).where(PhoneModel.id == phone_model_id))
    phone_mdl_parm = result.scalar_one()
    image_tasks = [
        utils.generate_image_async(prompt, phone_mdl_parm.phone_height, phone_mdl_parm.phone_width), # type: ignore
        utils.generate_image_async(prompt, phone_mdl_parm.phone_height, phone_mdl_parm.phone_width), # type: ignore
        utils.generate_image_async(prompt, phone_mdl_parm.phone_height, phone_mdl_parm.phone_width)  # type: ignore
    ]
    images = await asyncio.gather(*image_tasks)
    
    # Create an in-memory ZIP file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for idx, img in enumerate(images):
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            zip_file.writestr(f"image_{idx+1}.png", img_bytes.read())
            
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": "attachment; filename=generated_images.zip"}
    )

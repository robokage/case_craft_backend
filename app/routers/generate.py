from typing import Annotated
from fastapi import APIRouter, Depends, BackgroundTasks, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import SessionLocal
from uuid import uuid4

from app.schemas import PromptInput
from app.models import PhoneModel
from scripts.utils import Utils
from scripts.auth import AuthUtils


router = APIRouter()
utils = Utils()
auth_utils = AuthUtils()


async def get_db():
    async with SessionLocal() as sl:
        yield sl


db_dependency = Annotated[AsyncSession, Depends(get_db)]


@router.post("/anon/prompt-only")
async def generate_with_just_prompt_anon(
    payload: PromptInput , request: Request,bg_tasks: BackgroundTasks, db: db_dependency
    ):
    anon_id = request.cookies.get("anon_id")
    if not anon_id:
            anon_id = str(uuid4())
    utils.validate_max_gen_anon(anon_id)
    result = await db.execute(select(PhoneModel).where(PhoneModel.id == payload.phone_model_id))
    phone_mdl_parm = result.scalar_one_or_none()
    if not phone_mdl_parm:
        raise HTTPException(status_code=404, detail="User with given email already exists")
    return_data = await utils.handle_generation(prompt=payload.prompt,
                                                phone_height=phone_mdl_parm.phone_height, #type: ignore
                                                phone_width=phone_mdl_parm.phone_width, #type: ignore
                                                model_id=phone_mdl_parm.id, #type: ignore
                                                brand_id=phone_mdl_parm.brand_id, #type: ignore
                                                bg_tasks=bg_tasks)
    response = JSONResponse(content=return_data)
    response.set_cookie(key="anon_id", value=anon_id, max_age=60*60*24*30)
    return response


@router.post("/user/prompt-only")
async def generate_with_just_prompt(
    payload: PromptInput, 
    bg_tasks: BackgroundTasks, 
    db: db_dependency, 
    user_id: str = Depends(auth_utils.get_current_user_id)
    ):
    result = await db.execute(select(PhoneModel).where(PhoneModel.id == payload.phone_model_id))
    phone_mdl_parm = result.scalar_one_or_none()
    if not phone_mdl_parm:
        raise HTTPException(status_code=404, detail="User with given email already exists")
    return_data = await utils.handle_generation(prompt=payload.prompt,
                                                phone_height=phone_mdl_parm.phone_height, #type: ignore
                                                phone_width=phone_mdl_parm.phone_width, #type: ignore
                                                model_id=phone_mdl_parm.id, #type: ignore
                                                brand_id=phone_mdl_parm.brand_id, #type: ignore
                                                bg_tasks=bg_tasks)
    return return_data


@router.get("/get-download-link/{img_uuid}")
async def get_download_link(img_uuid: str):
    download_link = utils.get_image_download_link(img_uuid)
    if not download_link or download_link == "None":
        raise HTTPException(404, detail="Could not find the specified image. It may have been expired")
    return download_link
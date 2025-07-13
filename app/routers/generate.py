from typing import Annotated
from fastapi import APIRouter, Depends, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import SessionLocal
from uuid import uuid4

from app.schemas import PromptInput
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
    return_data = await utils.handle_generation(
        payload.prompt, payload.phone_model_id, db, bg_tasks)
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
    return_data = await utils.handle_generation(
         payload.prompt, payload.phone_model_id, db, bg_tasks)
    return return_data

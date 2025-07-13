from typing import Annotated
from fastapi import APIRouter, Depends, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import SessionLocal
from uuid import uuid4

from scripts.utils import Utils
from scripts.auth import AuthUtils


router = APIRouter()
utils = Utils()
auth_utils = AuthUtils()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_db():
    async with SessionLocal() as sl:
        yield sl


db_dependency = Annotated[AsyncSession, Depends(get_db)]


@router.post("/anon/prompt-only")
async def generate_with_just_prompt_anon(
    prompt: str, 
    phone_model_id:str , 
    request: Request,
    bg_tasks: BackgroundTasks, 
    db: db_dependency
):
    anon_id = request.cookies.get("anon_id")
    if not anon_id:
            anon_id = str(uuid4())
    utils.validate_max_gen_anon(anon_id)
    return_data = await utils.handle_generation(prompt, phone_model_id, db, bg_tasks)
    response = JSONResponse(content=return_data)
    response.set_cookie(key="anon_id", value=anon_id, max_age=60*60*24*30)
    return response


@router.post("/user/prompt-only")
async def generate_with_just_prompt(
    prompt: str, 
    phone_model_id:str , 
    bg_tasks: BackgroundTasks, 
    db: db_dependency, 
    token: str = Depends(oauth2_scheme)
    ):
    auth_utils.get_current_user_id(token)
    return_data = await utils.handle_generation(prompt, phone_model_id, db, bg_tasks)
    return return_data

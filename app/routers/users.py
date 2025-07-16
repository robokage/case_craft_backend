from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import status
from app.models import UserModel
from app.schemas import UserCreate, UserLogin
from app.db import SessionLocal
from scripts.utils import Utils
from scripts.auth import AuthUtils
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession



user_router = APIRouter()
utils = Utils()
auth_utils = AuthUtils()

async def get_db():
    async with SessionLocal() as sl:
        yield sl

db_dependency = Annotated[AsyncSession, Depends(get_db)]

@user_router.post("/user-signup")
async def user_sign_up(user_data: UserCreate, db: db_dependency):
    result = await db.execute(select(UserModel).where(UserModel.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User with given email already exists")
    
    hashed_pass = utils.hash_password(user_data.password)
    new_user = UserModel(email=user_data.email, 
                         name=user_data.name, 
                         password=hashed_pass)
    db.add(new_user)
    await db.commit()
    user_id = str(new_user.public_id)
    await db.close()
    return {"message": "User created", "user_id": user_id}

@user_router.post("/user-login")
async def user_log_in(db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()):
    user_data = UserLogin(email=form_data.username, password=form_data.password)
    result = await db.execute(select(UserModel).where(UserModel.email == user_data.email))
    user = result.scalar_one_or_none()
    if not user or not  utils.verify_pass_word(user_data.password, user.password): #type: ignore
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    token_data = {"public_id": str(user.public_id), "name": user.name, "email": user.email}
    jwt_token = auth_utils.create_access_token(data=token_data)
    return {"access_token": jwt_token, "token_type": "bearer"}
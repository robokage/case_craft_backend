import os
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import status
from app.models import UserModel, AuthProvider
from app.schemas import UserCreate, UserLogin, PasswordResetRequest, ResetPassword
from app.db import SessionLocal
from scripts.utils import Utils
from scripts.auth import AuthUtils
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode



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
    await db.close()
    return {"message": "User created successfully"}

@user_router.post("/user-login")
async def user_log_in(db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user_data = UserLogin(email=form_data.username, password=form_data.password)
    except ValidationError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                            detail=ve.errors()[0].get('ctx').get('reason')) #type: ignore
    result = await db.execute(select(UserModel).where(UserModel.email == user_data.email))
    user = result.scalar_one_or_none()
    if not user or not  utils.verify_pass_word(user_data.password, user.password): #type: ignore
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    token_data = {"public_id": str(user.public_id), "name": user.name, "email": user.email}
    jwt_token = auth_utils.create_access_token(data=token_data)
    return {"access_token": jwt_token, "token_type": "bearer"}


@user_router.get("/google-login")
async def google_login(request : Request):
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    return await auth_utils.google_oauth.google.authorize_redirect(request, redirect_uri) #type: ignore


@user_router.get("/google/callback")
async def google_callback(request: Request, db: db_dependency):
    token = await auth_utils.google_oauth.google.authorize_access_token(request) #type: ignore
    user_info = token.get("userinfo")
    if not user_info or "accounts.google.com" not in user_info.get("iss"):
        raise HTTPException(status_code=400, detail="Failed to fetch user info")
    result = await db.execute(select(UserModel).where(UserModel.email == user_info.get("email")))
    new_user = result.scalar_one_or_none()
    if not new_user:
        new_user = UserModel(email=user_info.get('email'),
                            name=user_info.get('name'),
                            auth_provider="google",
                            provider_user_id=user_info.get("sub"))
        db.add(new_user)
        await db.commit()
        await db.close()
    token_data = {"public_id": str(new_user.public_id), 
                  "name": new_user.name}
    jwt_token = auth_utils.create_access_token(data=token_data)
    params = urlencode({"access_token": jwt_token, "token_type": "bearer"})
    return RedirectResponse(url=f"{os.getenv('FRONTEND_URL')}/google/callback?{params}")


@user_router.post("/send-password-reset-mail")
async def send_password_reset_mail(req_data: PasswordResetRequest, db:db_dependency):
    result = await db.execute(select(UserModel).where(UserModel.email == req_data.email))
    user_data = result.scalar_one_or_none()
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Could not find User. Kindly create a new account")
    if user_data.auth_provider != AuthProvider.local: #type: ignore
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                            detail=f"This account is connected via {str(user_data.auth_provider).capitalize()}. Use that to sign in or reset password")
    reset_link = auth_utils.get_reset_link(user_data.email)  #type: ignore
    utils.send_reset_mail(to_email=user_data.email, reset_link=reset_link) #type: ignore
    return {"message": "Password reset link sent"}


@user_router.post("/reset-password")
async def reset_password(data: ResetPassword, db: db_dependency):
    user_email = auth_utils.validate_reset_token(token=data.token)
    result = await db.execute(select(UserModel).where(UserModel.email == user_email))
    user_data = result.scalar_one_or_none()
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Could not find User")
    user_data.password = utils.hash_password(data.new_password) #type: ignore
    await db.commit()
    auth_utils.delete_reset_token(data.token)
    return {"message": "Your password has been successfully reset"}
    
import os
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.phones import router as phone_router
from app.routers.generate import router as gen_router
from app.routers.users import user_router

app = FastAPI()
app.include_router(phone_router, prefix="/phones")
app.include_router(gen_router, prefix="/generate")
app.include_router(user_router, prefix="/user")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.casecraft.space"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY")) #type: ignore

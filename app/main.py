from dotenv import load_dotenv
load_dotenv() 


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
    allow_origins=["*"],  # Or ["http://localhost:3000"] if using specific frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
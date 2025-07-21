import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from fastapi import HTTPException


def password_validator(password):
    errors = []
    if len(password) < 8:
        errors.append("8 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("one uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("one lowercase letter")
    if not re.search(r"\d", password):
        errors.append("one number")
    if not re.search(r"[\W_]", password):
        errors.append("one special character")

    if errors:
        raise HTTPException(status_code=400, 
                            detail="Password must contain at least: " + ",".join(errors))


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    password: str
    
    @field_validator("password")
    def strong_password(cls, v):
        password_validator(v)
        return v


class PromptInput(BaseModel):
    prompt: str
    phone_model_id: str

class PasswordResetRequest(BaseModel):
    email: str

class ResetPassword(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    def strong_password(cls, v):
        password_validator(v)
        return v
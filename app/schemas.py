import re
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    password: str
    
    @field_validator("password")
    def strong_password(cls, v):
        errors = []
        if len(v) < 8:
            errors.append("8 characters")
        if not re.search(r"[A-Z]", v):
            errors.append("one uppercase letter")
        if not re.search(r"[a-z]", v):
            errors.append("one lowercase letter")
        if not re.search(r"\d", v):
            errors.append("one number")
        if not re.search(r"[\W_]", v):
            errors.append("one special character")

        if errors:
            raise ValueError("Password must contain at least: " + ", ".join(errors))
        return v


class PromptInput(BaseModel):
    prompt: str
    phone_model_id: str
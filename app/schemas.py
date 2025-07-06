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
        if not len(v) >= 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[\W_]", v):
            raise ValueError("Password must contain at least one special character")
        return v
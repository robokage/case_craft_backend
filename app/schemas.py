from fastapi_users import schemas

class UserRead(schemas.BaseUser[int]):
    full_name: str | None

class UserCreate(schemas.BaseUserCreate):
    full_name: str | None

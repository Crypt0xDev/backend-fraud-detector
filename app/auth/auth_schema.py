from typing import Literal

from pydantic import BaseModel

from app.user.user_schema import Role


class TokenOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class UserOut(BaseModel):
    username: str
    role: Role

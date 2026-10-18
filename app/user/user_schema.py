from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Role = Literal["admin", "user"]
ROLES: tuple[Role, ...] = ("admin", "user")
DEFAULT_ROLE: Role = "user"


class UserAccountOut(BaseModel):
    username: str
    role: Role
    created_at: datetime


class UserCreateIn(BaseModel):
    username: str = Field(min_length=1)
    password: str
    role: Role = DEFAULT_ROLE


class UserUpdateIn(BaseModel):
    role: Role | None = None
    password: str | None = None

from typing import Literal

from pydantic import BaseModel


class TokenOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class UserOut(BaseModel):
    username: str
    root: bool
    # Por ejemplo {"lotes": ["ver"]}; el root los recibe todos
    permissions: dict[str, list[str]] = {}

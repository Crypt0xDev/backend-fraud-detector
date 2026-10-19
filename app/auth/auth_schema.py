from typing import Literal

from pydantic import BaseModel, computed_field

from app.user.user_schema import Role


class TokenOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class UserOut(BaseModel):
    username: str
    root: bool
    # Por ejemplo {"lotes": ["ver"]}; el root los recibe todos
    permissions: dict[str, list[str]] = {}

    @computed_field(deprecated="Usa root y permissions")
    @property
    def role(self) -> Role:
        """Para el frontend anterior: admin si es root, si no user"""
        return "admin" if self.root else "user"

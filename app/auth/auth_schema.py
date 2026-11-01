# python
from typing import Literal

# pydantic
from pydantic import BaseModel


# Inicio del response del login
class TokenOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
# Fin del response del login


# Inicio del response de la sesión
class UserOut(BaseModel):
    username: str
    root: bool
    # Por ejemplo {"lotes": ["ver"]}; el root los recibe todos
    permissions: dict[str, list[str]] = {}
# Fin del response de la sesión

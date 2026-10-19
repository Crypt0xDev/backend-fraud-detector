import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ValidationInfo, computed_field, field_validator

from app.role.role_schema import SchemaRoleBasic
from utils.password import MIN_PASSWORD_LENGTH

Role = Literal["admin", "user"]
ROLES: tuple[Role, ...] = ("admin", "user")

UserState = Literal["Activo", "Inactivo"]
ACTIVE: UserState = "Activo"
INACTIVE: UserState = "Inactivo"

# Va en la URL (/users/{username}): sin "/", espacios ni nombres como ".."
USERNAME_CHARS = re.compile(r"[\w.@-]+")


def check_username(username: str) -> str:
    if not USERNAME_CHARS.fullmatch(username) or set(username) == {"."}:
        raise ValueError("Usa solo letras, números, puntos, guiones, _ o @")
    return username


class BaseSchema(BaseModel):
    model_config = {
        "str_strip_whitespace": True,
        "extra": "forbid",
    }


# Inicio del registro de un usuario
class SchemaCreate(BaseSchema):
    username: str = Field(..., min_length=1, max_length=150)
    password: str = Field(..., min_length=MIN_PASSWORD_LENGTH)
    root: bool = False
    # Si no se envían roles, se le da Analista
    role_ids: list[int] = Field(default_factory=list)
    role: Role | None = Field(None, deprecated="Usa root: admin equivale a root=true")

    @field_validator("username")
    @classmethod
    def valid_username(cls, v: str) -> str:
        return check_username(v)

    @field_validator("role_ids")
    @classmethod
    def ids_must_be_unique(cls, v: list[int]) -> list[int]:
        if len(v) != len(set(v)):
            raise ValueError("Los role_ids no pueden repetirse")
        return v


# Fin del registro de un usuario


# Inicio del actualizar
class SchemaUpdate(BaseSchema):
    password: str | None = Field(None, min_length=MIN_PASSWORD_LENGTH)
    root: bool | None = None
    # Reemplaza los roles del usuario por estos
    role_ids: list[int] | None = None
    role: Role | None = Field(None, deprecated="Usa root: admin equivale a root=true")

    @field_validator("role_ids")
    @classmethod
    def ids_must_be_unique(cls, v: list[int] | None) -> list[int] | None:
        if v is not None and len(v) != len(set(v)):
            raise ValueError("Los role_ids no pueden repetirse")
        return v


# Fin del actualizar


# Inicio del cambio de contraseña
class SchemaChangePassword(BaseSchema):
    current_password: str
    new_password: str = Field(..., min_length=MIN_PASSWORD_LENGTH)
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info: ValidationInfo) -> str:
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Las contraseñas no coinciden")
        return v


# Fin del cambio de contraseña


# Inicio del response
class SchemaResponse(BaseModel):
    username: str
    root: bool
    roles: list[SchemaRoleBasic] = []
    state: UserState
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}

    @computed_field(deprecated="Usa root y roles")
    @property
    def role(self) -> Role:
        """Para el frontend anterior: admin si es root, si no user"""
        return "admin" if self.root else "user"


# Fin del response

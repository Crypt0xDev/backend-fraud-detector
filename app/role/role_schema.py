from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

# Rol que se le da a un usuario si no se elige otro
ANALYST_ROLE = "Analista"


class BaseSchema(BaseModel):
    model_config = {
        "str_strip_whitespace": True,
        "extra": "forbid",
    }


# Inicio del registro de un rol
class SchemaRoleCreate(BaseSchema):
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=3, max_length=500)
    module_permission_ids: list[int] = Field(default_factory=list)

    @field_validator("module_permission_ids")
    @classmethod
    def ids_must_be_unique(cls, v: list[int]) -> list[int]:
        if len(v) != len(set(v)):
            raise ValueError("Los IDs de permisos no pueden repetirse")
        return v


# Fin del registro de un rol


# Inicio del actualizar
class SchemaRoleUpdate(SchemaRoleCreate):
    pass


# Fin del actualizar


# Inicio del response
class SchemaRoleBasic(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class SchemaRoleResponse(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    updated_at: datetime | None = None
    module_permission_ids: list[int] = []
    # Por ejemplo {"lotes": ["ver", "eliminar"]}
    permissions: dict[str, list[str]] = {}


# Fin del response


# Inicio del árbol de módulos con permisos
class ModulePermissionItemResponse(BaseModel):
    id: int
    name: str


class ModuleTreeResponse(BaseModel):
    """Módulo del árbol: hijos si es padre, si no permisos"""

    id: int
    code: str
    name: str
    icon: str | None = None
    is_parent: bool
    path: str | None = None
    permissions: list[ModulePermissionItemResponse] = []
    children: list[ModuleTreeResponse] = []

    @classmethod
    def build_tree(
        cls, modules: list, parent_id: int | None = None
    ) -> list[ModuleTreeResponse]:
        """Arma el árbol a partir de la lista de módulos"""
        return [
            cls(
                id=module.id,
                code=module.code,
                name=module.name,
                icon=module.icon,
                is_parent=module.is_parent,
                path=None if module.is_parent else module.path,
                permissions=[]
                if module.is_parent
                else [
                    ModulePermissionItemResponse(id=mp.id, name=mp.permission.name)
                    for mp in module.module_permissions
                ],
                children=cls.build_tree(modules, module.id) if module.is_parent else [],
            )
            for module in modules
            if module.parent_id == parent_id
        ]


ModuleTreeResponse.model_rebuild()
# Fin del árbol de módulos con permisos

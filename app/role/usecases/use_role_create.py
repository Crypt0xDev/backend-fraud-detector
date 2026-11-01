from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.role.role_entity import Role, RolePermission
from app.role.role_schema import ROLE_DELETED, SchemaRoleCreate
from app.role.usecases.use_role_permissions import commit_unique_name, validate_module_permission_ids


def execute(db: Session, role: SchemaRoleCreate) -> None:
    # Verificar que el nombre no esté en uso; los roles eliminados lo dejan libre
    if db.scalars(select(Role.id).where(Role.name == role.name, Role.state != ROLE_DELETED)).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un rol con ese nombre"
        )

    # Verificar que los IDs de permisos existan
    validate_module_permission_ids(db, role.module_permission_ids)

    db_role = Role(name=role.name, description=role.description)
    db_role.role_permissions = [RolePermission(module_permission_id=mp_id) for mp_id in role.module_permission_ids]
    db.add(db_role)

    # Si dos altas llegan a la vez, el UNIQUE del nombre frena la segunda
    commit_unique_name(db, role.name)

from sqlalchemy.orm import Session

from app.role.role_entity import Role, RolePermission
from app.role.role_schema import SchemaRoleCreate, SchemaRoleResponse
from app.role.usecases.use_role_permissions import (
    commit_unique_name,
    to_response,
    validate_module_permission_ids,
)
from app.user.user_entity import User


def execute(
    db: Session, current_user: User, role: SchemaRoleCreate
) -> SchemaRoleResponse:
    # Validar que los IDs de permisos existen
    validate_module_permission_ids(db, role.module_permission_ids)

    db_role = Role(name=role.name, description=role.description)
    db_role.role_permissions = [
        RolePermission(module_permission_id=mp_id)
        for mp_id in role.module_permission_ids
    ]
    db.add(db_role)
    # Nombre único
    commit_unique_name(db, role.name)
    db.refresh(db_role)
    return to_response(db_role)

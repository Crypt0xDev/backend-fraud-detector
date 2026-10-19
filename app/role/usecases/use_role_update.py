from sqlalchemy.orm import Session

from app.role.role_entity import Role, RolePermission
from app.role.role_schema import SchemaRoleResponse, SchemaRoleUpdate
from app.role.usecases.use_role_permissions import (
    commit_unique_name,
    to_response,
    validate_module_permission_ids,
)
from app.user.user_entity import User
from utils.helpers import utcnow


def execute(
    db: Session, current_user: User, role_id: int, role_data: SchemaRoleUpdate
) -> SchemaRoleResponse | None:
    db_role = db.query(Role).filter(Role.id == role_id).first()
    if db_role is None:
        return None

    # Validar que los IDs de permisos existen
    validate_module_permission_ids(db, role_data.module_permission_ids)

    # Se reutilizan los permisos que ya tenía para no duplicarlos
    current = {rp.module_permission_id: rp for rp in db_role.role_permissions}
    db_role.name = role_data.name
    db_role.description = role_data.description
    db_role.role_permissions = [
        current.get(mp_id) or RolePermission(module_permission_id=mp_id)
        for mp_id in role_data.module_permission_ids
    ]
    db_role.updated_at = utcnow()
    # Nombre único
    commit_unique_name(db, role_data.name)
    db.refresh(db_role)
    return to_response(db_role)

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.role.role_entity import Role, RolePermission
from app.role.role_schema import ANALYST_ROLE, ROLE_DELETED, SchemaRoleResponse, SchemaRoleUpdate
from app.role.usecases.use_role_permissions import commit_unique_name, to_response, validate_module_permission_ids
from utils.helpers import utcnow


def execute(db: Session, role_id: int, role_data: SchemaRoleUpdate) -> SchemaRoleResponse | None:
    db_role = db.scalars(select(Role).where(Role.id == role_id, Role.state != ROLE_DELETED)).first()

    if db_role is None:
        return None

    # Verificar que no se renombre el rol por defecto: se busca por su nombre
    if db_role.name == ANALYST_ROLE and role_data.name != ANALYST_ROLE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El rol {ANALYST_ROLE} no se puede renombrar: es el que reciben los usuarios nuevos"
        )

    # Verificar que los IDs de permisos existan
    validate_module_permission_ids(db, role_data.module_permission_ids)

    # Se reutilizan los permisos que ya tenía para no duplicarlos
    current = {rp.module_permission_id: rp for rp in db_role.role_permissions}
    db_role.name = role_data.name
    db_role.description = role_data.description
    db_role.role_permissions = [current.get(mp_id) or RolePermission(module_permission_id=mp_id) for mp_id in role_data.module_permission_ids]
    db_role.updated_at = utcnow()

    # Verificar que el nombre sea único al guardar
    commit_unique_name(db, role_data.name)
    db.refresh(db_role)
    return to_response(db_role)

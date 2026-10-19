from sqlalchemy.orm import Session

from app.role.role_entity import Role
from app.role.role_schema import SchemaRoleResponse
from app.role.usecases.use_role_permissions import (
    role_not_found,
    to_response,
    with_permissions,
)


def execute(db: Session, role_id: int) -> SchemaRoleResponse:
    role = db.query(Role).options(with_permissions()).filter(Role.id == role_id).first()
    if role is None:
        raise role_not_found()
    return to_response(role)

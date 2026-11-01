from sqlalchemy import select
from sqlalchemy.orm import Session

from app.role.role_entity import Role
from app.role.role_schema import ROLE_DELETED, SchemaRoleResponse
from app.role.usecases.use_role_permissions import to_response, with_permissions


def execute(db: Session, role_id: int) -> SchemaRoleResponse | None:
    role = db.scalars(select(Role).options(with_permissions()).where(Role.id == role_id, Role.state != ROLE_DELETED)).first()

    if role is None:
        return None

    return to_response(role)

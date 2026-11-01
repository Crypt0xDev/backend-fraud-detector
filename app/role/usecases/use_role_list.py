from sqlalchemy import select
from sqlalchemy.orm import Session

from app.role.role_entity import Role
from app.role.role_schema import ROLE_DELETED, SchemaRoleResponse
from app.role.usecases.use_role_permissions import to_response, with_permissions


def execute(db: Session) -> list[SchemaRoleResponse]:
    roles = db.scalars(select(Role).options(with_permissions()).where(Role.state != ROLE_DELETED).order_by(Role.name)).all()
    return [to_response(role) for role in roles]

from sqlalchemy.orm import Session

from app.role.role_entity import Role
from app.role.role_schema import SchemaRoleResponse
from app.role.usecases.use_role_permissions import to_response, with_permissions
from app.user.user_entity import User


def execute(db: Session, current_user: User) -> list[SchemaRoleResponse]:
    roles = db.query(Role).options(with_permissions()).order_by(Role.name).all()
    return [to_response(role) for role in roles]

from sqlalchemy.orm import Session

from app.role.role_entity import Role
from app.role.role_schema import SchemaRoleResponse
from app.role.usecases.use_role_permissions import to_response, with_permissions
from app.user.user_entity import User


def execute(db: Session, current_user: User, role_id: int) -> SchemaRoleResponse | None:
    role = db.query(Role).options(with_permissions()).filter(Role.id == role_id).first()
    return to_response(role) if role else None

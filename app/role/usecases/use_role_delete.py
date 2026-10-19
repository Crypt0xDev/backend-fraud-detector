from sqlalchemy.orm import Session

from app.role.role_entity import Role
from app.role.usecases.use_role_permissions import role_not_found
from app.user.user_entity import UserRole
from utils.errors import ConflictError


def execute(db: Session, role_id: int) -> None:
    db_role = db.query(Role).filter(Role.id == role_id).first()
    if db_role is None:
        raise role_not_found()

    # Si algún usuario tiene el rol no se borra, porque se quedaría sin permisos
    assigned = db.query(UserRole).filter(UserRole.role_id == role_id).count()
    if assigned:
        raise ConflictError(
            f"El rol está asignado a {assigned} usuario(s); quítaselo primero"
        )

    db.delete(db_role)
    db.commit()

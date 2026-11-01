from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.role.role_entity import Role
from app.role.role_schema import ANALYST_ROLE, ROLE_DELETED
from app.user.user_entity import User, UserRole
from app.user.user_schema import DELETED
from utils.helpers import utcnow


def execute(db: Session, role_id: int) -> bool:
    db_role = db.scalars(select(Role).where(Role.id == role_id, Role.state != ROLE_DELETED)).first()

    if db_role is None:
        return False

    # Verificar que no sea el rol que se da por defecto a los usuarios nuevos
    if db_role.name == ANALYST_ROLE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El rol {ANALYST_ROLE} no se puede eliminar: es el que reciben los usuarios nuevos"
        )

    # Verificar que no esté asignado a ningún usuario activo
    assigned = db.scalar(
        select(func.count())
        .select_from(UserRole)
        .join(User, User.username == UserRole.username)
        .where(UserRole.role_id == role_id, User.state != DELETED)
    ) or 0
    if assigned:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El rol está asignado a {assigned} usuario(s); quítaselo primero"
        )

    # Borrado lógico: el rol y sus permisos se quedan guardados
    db_role.state = ROLE_DELETED
    db_role.deleted_at = utcnow()
    db.commit()
    return True

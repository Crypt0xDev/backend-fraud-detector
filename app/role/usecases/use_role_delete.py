from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.role.role_entity import Role
from app.user.user_entity import User, UserRole


def execute(db: Session, current_user: User, role_id: int) -> bool:
    db_role = db.query(Role).filter(Role.id == role_id).first()
    if db_role is None:
        return False

    # Si algún usuario tiene el rol no se borra, porque se quedaría sin permisos
    assigned = db.query(UserRole).filter(UserRole.role_id == role_id).count()
    if assigned:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El rol está asignado a {assigned} usuario(s); quítaselo primero",
        )

    db.delete(db_role)
    db.commit()
    return True

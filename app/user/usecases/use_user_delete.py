from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.user.usecases.use_user_roles import ensure_not_last_root
from app.user.user_entity import User
from app.user.user_schema import DELETED
from utils.helpers import utcnow


def execute(db: Session, current_user: User, username: str) -> bool:
    if current_user.username == username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No puedes eliminarte a ti mismo"
        )

    db_user = db.scalars(select(User).where(User.username == username, User.state != DELETED)).first()

    if db_user is None:
        return False

    # Verificar que no se elimine al último root
    ensure_not_last_root(db, db_user)

    # Borrado lógico: sus lotes y predicciones se quedan guardados
    db_user.state = DELETED
    db_user.deleted_at = utcnow()
    # Cierra sus sesiones abiertas
    db_user.token_version += 1
    db.commit()
    return True

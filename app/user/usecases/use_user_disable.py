from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.user.usecases.use_user_roles import ensure_not_last_root
from app.user.user_entity import User
from app.user.user_schema import ACTIVE, DISABLED
from utils.helpers import utcnow


def execute(db: Session, current_user: User, username: str) -> bool:
    if current_user.username == username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No puedes deshabilitarte a ti mismo"
        )

    user = db.scalars(select(User).where(User.username == username, User.state == ACTIVE)).first()

    if user is None:
        return False

    # Verificar que no se deshabilite al último root
    ensure_not_last_root(db, user)

    user.state = DISABLED
    # Si se vuelve a habilitar, los tokens de antes ya no sirven
    user.token_version += 1
    user.updated_at = utcnow()
    db.commit()
    return True

from sqlalchemy.orm import Session

from app.user.usecases.use_user_roles import ensure_not_last_root, user_not_found
from app.user.user_entity import User
from app.user.user_schema import ACTIVE, INACTIVE
from utils.errors import ConflictError
from utils.helpers import utcnow


def execute(db: Session, current_user: User, username: str) -> None:
    """Deshabilitar un usuario sin borrar sus datos"""
    db_user = (
        db.query(User).filter(User.username == username, User.state == ACTIVE).first()
    )
    if db_user is None:
        raise user_not_found("Usuario no encontrado o ya está deshabilitado")

    # Verificar que no se deshabilite a sí mismo ni al último root
    if username == current_user.username:
        raise ConflictError("No puedes deshabilitar tu propio usuario")
    ensure_not_last_root(db, db_user)

    db_user.state = INACTIVE
    # Si se vuelve a habilitar, los tokens de antes ya no sirven
    db_user.token_version += 1
    db_user.updated_at = utcnow()
    db.commit()

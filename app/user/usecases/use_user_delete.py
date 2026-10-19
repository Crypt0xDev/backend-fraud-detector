from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.user.usecases.use_user_roles import ensure_not_last_root, user_not_found
from app.user.user_entity import User
from app.user.user_port import UserDataCleaner
from utils.errors import ConflictError, StorageFailureError
from utils.storage import StorageError


def execute(
    db: Session,
    current_user: User,
    username: str,
    cleaners: Sequence[UserDataCleaner],
) -> None:
    """Borra el usuario"""
    db_user = db.query(User).filter(User.username == username).first()
    if db_user is None:
        raise user_not_found()

    # Verificar que no se borre a sí mismo ni al último root
    if username == current_user.username:
        raise ConflictError("No puedes borrar tu propio usuario")
    ensure_not_last_root(db, db_user)

    # Borrar los archivos del usuario antes que la cuenta
    try:
        for cleaner in cleaners:
            cleaner.delete_user_data(db, username)
    except StorageError as error:
        raise StorageFailureError(
            "No se pudieron borrar los archivos del usuario"
        ) from error

    db.delete(db_user)
    db.commit()

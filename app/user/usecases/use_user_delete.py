from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.user.usecases.use_user_roles import ensure_not_last_root
from app.user.user_entity import User
from app.user.user_port import UserDataCleaner
from utils.storage import StorageError


def execute(
    db: Session,
    current_user: User,
    username: str,
    cleaners: Sequence[UserDataCleaner],
) -> bool:
    """Borra el usuario"""
    db_user = db.query(User).filter(User.username == username).first()
    if db_user is None:
        return False

    # Verificar que no se borre a sí mismo ni al último root
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No puedes borrar tu propio usuario",
        )
    ensure_not_last_root(db, db_user)

    # Borrar los archivos del usuario antes que la cuenta
    try:
        for cleaner in cleaners:
            cleaner.delete_user_data(db, username)
    except StorageError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudieron borrar los archivos del usuario",
        ) from error

    db.delete(db_user)
    db.commit()
    return True

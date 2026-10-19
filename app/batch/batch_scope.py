from fastapi import HTTPException, status

from app.auth.auth_dependency import is_root
from app.batch.batch_entity import Batch
from app.user.user_entity import User


def visible_to(current_user: User) -> list:
    """Lotes que el usuario puede abrir o borrar. El root puede con todos"""
    return [] if is_root(current_user) else [Batch.username == current_user.username]


def requested_by(current_user: User, all: bool) -> list:
    """Lotes que se listan: los suyos, o todos si es root y pide `all`"""
    if all and not is_root(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un administrador puede ver los lotes de todos",
        )
    return [] if all else [Batch.username == current_user.username]

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.user.usecases.use_user_roles import (
    default_roles,
    ensure_not_last_root,
    resolve_roles,
)
from app.user.user_entity import User
from app.user.user_schema import SchemaUpdate
from utils.helpers import utcnow
from utils.password import hash_password


def execute(
    db: Session, current_user: User, username: str, user_data: SchemaUpdate
) -> User | None:
    root = user_data.root
    if root is None and user_data.role is not None:
        root = user_data.role == "admin"

    # Validar que se pida algún cambio
    if root is None and user_data.password is None and user_data.role_ids is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Indica una contraseña nueva, root o los roles",
        )

    db_user = db.query(User).filter(User.username == username).first()
    if db_user is None:
        return None

    # El root no puede quitarse el root a sí mismo ni dejar el sistema sin root
    if root is False and db_user.root:
        if username == current_user.username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No puedes quitarte tu propio acceso de administrador",
            )
        ensure_not_last_root(db, db_user)

    if user_data.password is not None:
        db_user.password_hash = hash_password(user_data.password)
        db_user.token_version += 1
    if root is not None:
        db_user.root = root
    if user_data.role_ids is not None:
        db_user.roles = resolve_roles(db, user_data.role_ids)
    elif root is False and not db_user.roles:
        # Si deja de ser root y no tiene roles, queda como Analista
        db_user.roles = default_roles(db)

    db_user.updated_at = utcnow()
    db.commit()
    db.refresh(db_user)
    return db_user

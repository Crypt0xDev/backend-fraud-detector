from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.user.usecases.use_user_roles import default_roles, resolve_roles
from app.user.user_entity import User
from app.user.user_schema import ACTIVE, SchemaCreate
from utils.password import hash_password


def username_taken(db: Session, username: str) -> bool:
    """True si otro usuario ya tiene ese nombre, sin distinguir mayúsculas (Admin = admin)"""
    query = select(User.username).where(func.lower(User.username) == username.lower())
    return db.scalars(query.limit(1)).first() is not None


def execute(db: Session, user: SchemaCreate) -> None:
    # Verificar que el nombre no esté en uso (también por un usuario eliminado)
    if username_taken(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario ya existe, elija otro nombre de usuario"
        )

    # Verificar que los roles existan
    roles = resolve_roles(db, user.role_ids) if user.role_ids else None

    db_user = User(
        username=user.username,
        password_hash=hash_password(user.password),
        root=user.root,
        state=ACTIVE,
    )
    # Si no se eligen roles se le da Analista (el root no necesita)
    if roles:
        db_user.roles = roles
    elif not user.root:
        db_user.roles = default_roles(db)
    db.add(db_user)

    # Si dos altas llegan a la vez, la clave primaria frena la segunda
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if db.get(User, user.username) is None:
            raise
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario ya existe, elija otro nombre de usuario"
        ) from error

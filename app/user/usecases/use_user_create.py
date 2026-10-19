from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.user.usecases.use_user_roles import default_roles, resolve_roles
from app.user.user_entity import User
from app.user.user_schema import ACTIVE, SchemaCreate
from utils.password import hash_password


def execute(db: Session, current_user: User, user: SchemaCreate) -> User:
    root = user.root or user.role == "admin"
    db_user = User(
        username=user.username,
        password_hash=hash_password(user.password),
        root=root,
        state=ACTIVE,
    )
    # Si no se eligen roles se le da Analista (el root no necesita)
    if user.role_ids:
        db_user.roles = resolve_roles(db, user.role_ids)
    elif not root:
        db_user.roles = default_roles(db)

    # La clave primaria decide si ya existe; así no falla con dos altas a la vez
    db.add(db_user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if db.get(User, user.username) is None:
            raise
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="El usuario ya existe"
        ) from error
    db.refresh(db_user)
    return db_user

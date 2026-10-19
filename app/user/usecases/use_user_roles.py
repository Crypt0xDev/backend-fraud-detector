from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.role.role_entity import Role
from app.role.role_schema import ANALYST_ROLE
from app.user.user_entity import User
from app.user.user_schema import ACTIVE


def resolve_roles(db: Session, role_ids: list[int]) -> list[Role]:
    """Busca los roles enviados; si alguno no existe da error 400"""
    roles = db.query(Role).filter(Role.id.in_(role_ids)).all() if role_ids else []
    missing = sorted(set(role_ids) - {role.id for role in roles})
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Los siguientes roles no existen: {missing}",
        )
    return roles


def default_roles(db: Session) -> list[Role]:
    """El rol Analista, que es el que se da si no se elige otro"""
    return db.query(Role).filter(Role.name == ANALYST_ROLE).all()


def ensure_not_last_root(db: Session, user: User) -> None:
    """No deja quitar al último root activo"""
    if not user.root or user.state != ACTIVE:
        return
    # FOR UPDATE: si dos roots se quitan entre sí a la vez, el segundo espera al
    # primero y ya no lo cuenta. Las filas quedan bloqueadas hasta el commit
    roots = (
        db.query(User.username)
        .filter(User.root.is_(True), User.state == ACTIVE)
        .with_for_update()
        .all()
    )
    if len(roots) <= 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Debe quedar al menos un administrador",
        )

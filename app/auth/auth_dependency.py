from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.module.module_entity import Module, ModulePermission
from app.permission.permission_entity import Permission
from app.role.role_entity import RolePermission
from app.user.user_entity import User, UserRole
from app.user.user_schema import ACTIVE
from config.database import get_db
from config.settings import API_PREFIX, settings
from utils.rate_limit import WINDOW_SECONDS, limiter
from utils.token import decode_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{API_PREFIX}/auth/login", auto_error=False
)


def get_current_user(
    token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesión no válida o expirada",
        headers={"WWW-Authenticate": "Bearer"},
    )
    claims = decode_token(token) if token else None
    if claims is None:
        raise credentials_exception
    username, version = claims

    # Si se deshabilita al usuario o cambia su contraseña, se cierran sus sesiones
    user = db.scalars(
        select(User).where(User.username == username, User.state == ACTIVE)
    ).first()
    if user is None or user.token_version != version:
        raise credentials_exception
    return user


def is_root(user: User) -> bool:
    return bool(user.root)


def get_current_root(current_user: User = Depends(get_current_user)) -> User:
    """Exige que el usuario sea root; se usa en las rutas de usuarios y roles"""
    if not is_root(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un administrador puede hacer esto",
        )
    return current_user


def user_permissions(db: Session, user: User) -> dict[str, list[str]]:
    """Permisos de todos los roles del usuario; el root los tiene todos"""
    # Los ids van en el SELECT porque PostgreSQL exige que DISTINCT incluya el ORDER BY
    query = (
        select(Module.code, Permission.name, Module.id, Permission.id)
        .join(ModulePermission, ModulePermission.module_id == Module.id)
        .join(Permission, Permission.id == ModulePermission.permission_id)
    )
    if not is_root(user):
        query = (
            query.join(
                RolePermission,
                RolePermission.module_permission_id == ModulePermission.id,
            )
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.username == user.username)
        )
    result: dict[str, list[str]] = {}
    for code, action, _, _ in db.execute(query.order_by(Module.id, Permission.id).distinct()):
        result.setdefault(code, []).append(action)
    return result


def has_permission(db: Session, user: User, module_code: str, action: str) -> bool:
    """True si alguno de sus roles le permite hacer esa acción en el módulo"""
    query = (
        select(UserRole.id)
        .join(RolePermission, RolePermission.role_id == UserRole.role_id)
        .join(
            ModulePermission, ModulePermission.id == RolePermission.module_permission_id
        )
        .join(Module, Module.id == ModulePermission.module_id)
        .join(Permission, Permission.id == ModulePermission.permission_id)
        .where(
            UserRole.username == user.username,
            Module.code == module_code,
            Permission.name == action,
        )
        .limit(1)
    )
    return db.scalars(query).first() is not None


def require_permission(module_code: str, action: str):
    """Exige el permiso en el módulo; el root siempre pasa"""

    def dependency(
        current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> User:
        if is_root(current_user):
            return current_user
        if not has_permission(db, current_user, module_code, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para esta acción",
            )
        return current_user

    return dependency


def rate_limit(current_user: User = Depends(get_current_user)) -> None:
    if not limiter.allow(current_user.username, settings.rate_limit_per_minute):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiadas solicitudes. Espera un minuto e inténtalo de nuevo.",
            headers={"Retry-After": str(int(WINDOW_SECONDS))},
        )


RateLimited = Depends(rate_limit)

# fastapi
from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# dependencias
from config.database import get_db
from config.settings import settings
from app.auth.auth_dependency import get_current_user, user_permissions

# casos de uso
from app.auth.usecases.use_auth_login import execute as login_execute

# entidades
from app.user.user_entity import User

# esquemas
from app.auth.auth_schema import TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

def client_ip(request: Request) -> str | None:
    """IP del navegador; detrás del frontend llega en X-Forwarded-For (la última es la que agregó el proxy)"""
    host = request.client.host if request.client else None
    if host in settings.trusted_proxies_set:
        forwarded = [ip.strip() for ip in request.headers.get("x-forwarded-for", "").split(",") if ip.strip()]
        if forwarded:
            return forwarded[-1]
    return host

@router.post("/login", response_model=TokenOut)
def login_endpoint(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Inicia sesión con usuario y contraseña; devuelve un token Bearer"""
    return login_execute(
        db=db,
        username=form.username,
        password=form.password,
        client_ip=client_ip(request),
    )

@router.get("/me", response_model=UserOut)
def me_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Usuario que inició sesión y sus permisos por módulo, para armar el menú"""
    return UserOut(
        username=current_user.username,
        root=current_user.root,
        permissions=user_permissions(db, current_user),
    )
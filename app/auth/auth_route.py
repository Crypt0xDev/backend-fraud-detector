# fastapi
from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# dependencias
from app.auth.auth_dependency import get_current_user, user_permissions

# esquemas
from app.auth.auth_schema import TokenOut, UserOut

# casos de uso
from app.auth.usecases.use_auth_login import execute as login_execute

# entidades
from app.user.user_entity import User
from config.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


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
        client_ip=request.client.host if request.client else None,
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

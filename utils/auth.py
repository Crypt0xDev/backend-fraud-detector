from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from app.user.user_repository import UserRepository
from utils.token import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_users(request: Request) -> UserRepository:
    users = request.app.state.users
    if users is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La base de datos de usuarios no está configurada",
        )
    return users


Users = Annotated[UserRepository, Depends(get_users)]


def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)], users: Users
) -> str:
    username = decode_token(token) if token else None
    if username is None or not users.exists(username):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión no válida o expirada",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username


CurrentUser = Annotated[str, Depends(get_current_user)]

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.auth_schema import TokenOut, UserOut
from app.auth.usecases.use_auth_login import InvalidCredentialsError, login
from app.user.user_schema import DEFAULT_ROLE
from utils.auth import CurrentUser, Users

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login_route(
    form: Annotated[OAuth2PasswordRequestForm, Depends()], users: Users
) -> TokenOut:
    try:
        return login(users, form.username, form.password)
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


@router.get("/me", response_model=UserOut)
def me_route(username: CurrentUser, users: Users) -> UserOut:
    return UserOut(username=username, role=users.get_role(username) or DEFAULT_ROLE)

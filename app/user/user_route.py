from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.user.usecases.use_user_create import (
    InvalidUserError,
    UserExistsError,
    register_user,
)
from app.user.usecases.use_user_delete import delete_user
from app.user.usecases.use_user_list import list_users
from app.user.usecases.use_user_update import (
    ProtectedUserError,
    UserNotFoundError,
    update_user,
)
from app.user.user_schema import UserAccountOut, UserCreateIn, UserUpdateIn
from utils.auth import CurrentAdmin, Users, get_current_admin
from utils.storage import StorageError

router = APIRouter(
    prefix="/users", tags=["users"], dependencies=[Depends(get_current_admin)]
)


def not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="El usuario no existe"
    )


def bad_request(error: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
    )


def conflict(error: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))


def find(users: Users, username: str) -> UserAccountOut:
    user = next((u for u in list_users(users) if u.username == username), None)
    if user is None:
        raise not_found()
    return user


@router.get("", response_model=list[UserAccountOut])
def list_route(users: Users) -> list[UserAccountOut]:
    return list_users(users)


@router.post("", response_model=UserAccountOut, status_code=status.HTTP_201_CREATED)
def create_route(payload: UserCreateIn, users: Users) -> UserAccountOut:
    try:
        register_user(users, payload.username, payload.password, payload.role)
    except UserExistsError as error:
        raise conflict(ValueError("El usuario ya existe")) from error
    except InvalidUserError as error:
        raise bad_request(error) from error
    return find(users, payload.username.strip())


@router.patch("/{username}", response_model=UserAccountOut)
def update_route(
    username: str, payload: UserUpdateIn, users: Users, admin: CurrentAdmin
) -> UserAccountOut:
    try:
        update_user(
            users,
            username,
            acting_admin=admin,
            role=payload.role,
            password=payload.password,
        )
    except UserNotFoundError as error:
        raise not_found() from error
    except InvalidUserError as error:
        raise bad_request(error) from error
    except ProtectedUserError as error:
        raise conflict(error) from error
    return find(users, username)


@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route(
    username: str, request: Request, users: Users, admin: CurrentAdmin
) -> Response:
    try:
        delete_user(
            users,
            request.app.state.batches,
            request.app.state.storage,
            username,
            acting_admin=admin,
        )
    except UserNotFoundError as error:
        raise not_found() from error
    except ProtectedUserError as error:
        raise conflict(error) from error
    except StorageError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudieron borrar los archivos del usuario",
        ) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)

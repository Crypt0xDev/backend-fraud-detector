from app.user.usecases.use_user_create import InvalidUserError, create_user
from app.user.user_repository import UserRepository
from app.user.user_schema import Role


class UserNotFoundError(Exception):
    pass


class ProtectedUserError(Exception):
    pass


def ensure_exists(users: UserRepository, username: str) -> None:
    if not users.exists(username):
        raise UserNotFoundError


def ensure_not_last_admin(users: UserRepository, username: str) -> None:
    if users.get_role(username) == "admin" and users.count_admins() <= 1:
        raise ProtectedUserError("Debe quedar al menos un administrador")


def update_user(
    users: UserRepository,
    username: str,
    *,
    acting_admin: str,
    role: Role | None = None,
    password: str | None = None,
) -> None:
    ensure_exists(users, username)
    if role is not None and role != "admin":
        if username == acting_admin:
            raise ProtectedUserError(
                "No puedes quitarte tu propio rol de administrador"
            )
        ensure_not_last_admin(users, username)
    if password is not None:
        create_user(users, username, password)
    elif role is None:
        raise InvalidUserError("Indica un rol o una contraseña nueva")
    if role is not None:
        users.set_role(username, role)

from app.user.user_repository import UserRepository
from app.user.user_schema import DEFAULT_ROLE, ROLES, Role
from utils.password import MIN_PASSWORD_LENGTH, hash_password


class InvalidUserError(ValueError):
    pass


def create_user(
    users: UserRepository, username: str, password: str, role: Role | None = None
) -> bool:
    """Crea el usuario o cambia su contraseña; devuelve True si es nuevo.

    Un usuario nuevo recibe `role` (por defecto "user"). En uno existente el rol solo
    cambia si se indica `role`.
    """
    username = username.strip()
    if not username:
        raise InvalidUserError("El usuario no puede estar vacío")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise InvalidUserError(
            f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres"
        )
    if role is not None and role not in ROLES:
        raise InvalidUserError(f"Rol no válido: {role}. Usa: {', '.join(ROLES)}")
    created = users.save(username, hash_password(password), role or DEFAULT_ROLE)
    if not created and role is not None:
        users.set_role(username, role)
    return created


class UserExistsError(Exception):
    pass


def register_user(
    users: UserRepository, username: str, password: str, role: Role
) -> None:
    """Alta desde la administración: a diferencia de create_user, no toca un usuario
    existente."""
    if users.exists(username.strip()):
        raise UserExistsError
    create_user(users, username, password, role)

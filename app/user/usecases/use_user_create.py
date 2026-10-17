from app.user.user_repository import UserRepository
from utils.password import MIN_PASSWORD_LENGTH, hash_password


class InvalidUserError(ValueError):
    pass


def create_user(users: UserRepository, username: str, password: str) -> bool:
    """Crea el usuario o cambia su contraseña; devuelve True si es nuevo."""
    username = username.strip()
    if not username:
        raise InvalidUserError("El usuario no puede estar vacío")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise InvalidUserError(
            f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres"
        )
    return users.save(username, hash_password(password))

import logging

from app.user.usecases.use_user_create import InvalidUserError, create_user
from app.user.user_repository import UserRepository
from app.user.user_schema import Role

logger = logging.getLogger(__name__)


def seed_account(
    users: UserRepository,
    username: str | None,
    password: str | None,
    role: Role,
    env_prefix: str,
) -> None:
    """Crea la cuenta si no existe. Si existe, nunca cambia su contraseña; solo le
    asegura el rol."""
    if not username or not password:
        return
    if users.exists(username):
        if users.get_role(username) != role:
            users.set_role(username, role)
            logger.info("Usuario %s ahora tiene rol %s", username, role)
        return
    try:
        create_user(users, username, password, role)
    except InvalidUserError as error:
        logger.error(
            "%s_USERNAME/%s_PASSWORD no válidos: %s", env_prefix, env_prefix, error
        )
        return
    logger.info("Usuario %s (%s) creado", username, role)

import logging

from app.user.usecases.use_user_create import InvalidUserError, create_user
from app.user.user_repository import UserRepository
from config.settings import settings

logger = logging.getLogger(__name__)


def seed_admin(users: UserRepository) -> None:
    """Crea el usuario de ADMIN_USERNAME si no existe; nunca cambia uno existente."""
    username, password = settings.admin_username, settings.admin_password
    if not username or not password or users.exists(username):
        return
    try:
        create_user(users, username, password)
    except InvalidUserError as error:
        logger.error("ADMIN_USERNAME/ADMIN_PASSWORD no válidos: %s", error)
        return
    logger.info("Usuario inicial %s creado", username)

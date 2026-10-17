import logging

from app.user.user_repository import UserRepository
from seeders.admin_seeder import seed_admin

logger = logging.getLogger(__name__)

SEEDERS = [seed_admin]


def create_default_records(users: UserRepository | None) -> None:
    if users is None:
        return
    for seeder in SEEDERS:
        try:
            seeder(users)
        except Exception:
            logger.exception("Falló el seeder %s", seeder.__name__)

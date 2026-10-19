from sqlalchemy.orm import Session

from config.seeders.seed_account import seed_account
from config.settings import settings


def seed_admin(db: Session) -> None:
    """Usuario root de ADMIN_USERNAME / ADMIN_PASSWORD."""
    seed_account(
        db,
        settings.admin_username,
        settings.admin_password,
        root=True,
        env_prefix="ADMIN",
    )


def seed_user(db: Session) -> None:
    """Usuario con rol Analista de USER_USERNAME / USER_PASSWORD."""
    seed_account(
        db,
        settings.user_username,
        settings.user_password,
        root=False,
        env_prefix="USER",
    )

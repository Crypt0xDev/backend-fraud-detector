from app.user.user_repository import UserRepository
from config.settings import settings
from seeders.account_seeder import seed_account


def seed_admin(users: UserRepository) -> None:
    """Usuario administrador de ADMIN_USERNAME / ADMIN_PASSWORD."""
    seed_account(
        users, settings.admin_username, settings.admin_password, "admin", "ADMIN"
    )

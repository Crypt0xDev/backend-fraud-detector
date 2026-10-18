from app.user.user_repository import UserRepository
from config.settings import settings
from seeders.account_seeder import seed_account


def seed_user(users: UserRepository) -> None:
    """Usuario normal de USER_USERNAME / USER_PASSWORD."""
    seed_account(users, settings.user_username, settings.user_password, "user", "USER")

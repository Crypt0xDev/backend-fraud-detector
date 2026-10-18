from app.user.user_repository import UserRepository
from app.user.user_schema import UserAccountOut


def list_users(users: UserRepository) -> list[UserAccountOut]:
    return users.list()

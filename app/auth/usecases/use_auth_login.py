from app.auth.auth_schema import TokenOut
from app.user.user_repository import UserRepository
from utils.password import DUMMY_HASH, verify_password
from utils.token import create_token


class InvalidCredentialsError(Exception):
    pass


def login(users: UserRepository, username: str, password: str) -> TokenOut:
    stored = users.get_password_hash(username)
    if not verify_password(password, stored or DUMMY_HASH) or stored is None:
        raise InvalidCredentialsError
    token, expires_in = create_token(username)
    return TokenOut(access_token=token, expires_in=expires_in)

import threading

from sqlalchemy.orm import Session

from app.auth.auth_schema import TokenOut
from app.user.user_entity import User
from app.user.user_schema import ACTIVE
from config.settings import settings
from utils.errors import AuthenticationError, RateLimitedError, UnavailableError
from utils.password import DUMMY_HASH, verify_password
from utils.rate_limit import WINDOW_SECONDS, limiter
from utils.token import create_token

LOGIN_ATTEMPTS_PER_MINUTE = 10

# Cada verificación usa 16 MiB y ~50 ms de CPU (scrypt): se limitan las simultáneas
# para que un aluvión de logins no se lleve la memoria ni todos los hilos
LOGIN_SLOTS = threading.BoundedSemaphore(4)
LOGIN_SLOT_TIMEOUT_SECONDS = 2.0


def too_many_attempts() -> RateLimitedError:
    return RateLimitedError(
        "Demasiados intentos. Espera un minuto e inténtalo de nuevo.",
        retry_after=int(WINDOW_SECONDS),
    )


def execute(
    db: Session, username: str, password: str, client_ip: str | None = None
) -> TokenOut:
    # Frena a quien prueba muchos usuarios desde la misma IP
    if client_ip and not limiter.allow(
        f"login-ip:{client_ip}", settings.login_rate_limit_per_ip
    ):
        raise too_many_attempts()
    # Frena a quien prueba contraseñas una tras otra
    if not limiter.allow(f"login:{username.lower()}", LOGIN_ATTEMPTS_PER_MINUTE):
        raise too_many_attempts()

    user = db.query(User).filter(User.username == username).first()

    if not LOGIN_SLOTS.acquire(timeout=LOGIN_SLOT_TIMEOUT_SECONDS):
        raise UnavailableError(
            "Hay demasiados inicios de sesión a la vez. Inténtalo de nuevo.",
            retry_after=1,
        )
    try:
        valid = verify_password(password, user.password_hash if user else DUMMY_HASH)
    finally:
        LOGIN_SLOTS.release()
    if not valid or user is None or user.state != ACTIVE:
        raise AuthenticationError("Usuario o contraseña incorrectos")

    token, expires_in = create_token(user.username, user.token_version)
    return TokenOut(access_token=token, expires_in=expires_in)

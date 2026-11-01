import threading

# FastAPI y SQLAlchemy
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

# Schemas y entidades
from app.auth.auth_schema import TokenOut
from app.user.user_entity import User
from app.user.user_schema import ACTIVE

# Configuración
from config.settings import settings

# Utilidades
from utils.password import DUMMY_HASH, verify_password
from utils.rate_limit import WINDOW_SECONDS, limiter
from utils.token import create_token

# Limitar intentos de inicio de sesión para evitar ataques de fuerza bruta
LOGIN_ATTEMPTS_PER_MINUTE = 10
LOGIN_SLOTS = threading.BoundedSemaphore(4)
LOGIN_SLOT_TIMEOUT_SECONDS = 2.0

def too_many_attempts():
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Demasiados intentos. Espera un minuto e inténtalo de nuevo.",
        headers={"Retry-After": str(int(WINDOW_SECONDS))}
    )

def execute(db: Session, username: str, password: str, client_ip: str | None = None):
    # Limitar intentos de inicio de sesión por IP y por usuario
    if client_ip and not limiter.allow(f"login-ip:{client_ip}", settings.login_rate_limit_per_ip):
        raise too_many_attempts()
    # Limitar intentos de inicio de sesión por usuario
    if not limiter.allow(f"login:{username.lower()}", LOGIN_ATTEMPTS_PER_MINUTE):
        raise too_many_attempts()

    user = db.get(User, username)

    # Limitar inicios de sesión simultáneos para evitar ataques de fuerza bruta
    if not LOGIN_SLOTS.acquire(timeout=LOGIN_SLOT_TIMEOUT_SECONDS):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hay demasiados inicios de sesión a la vez. Inténtalo de nuevo.",
            headers={"Retry-After": "1"}
        )
    try:
        valid = verify_password(password, user.password_hash if user else DUMMY_HASH)
    finally:
        LOGIN_SLOTS.release()
    if not valid or user is None or user.state != ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token, expires_in = create_token(user.username, user.token_version)
    return TokenOut(access_token=token, expires_in=expires_in)
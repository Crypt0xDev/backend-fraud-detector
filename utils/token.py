import logging
import secrets
from datetime import UTC, datetime, timedelta
from functools import cache

import jwt

from config.settings import settings

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"


@cache
def jwt_secret() -> str:
    if settings.jwt_secret:
        return settings.jwt_secret
    logger.warning("JWT_SECRET no está definido: las sesiones se pierden al reiniciar")
    return secrets.token_urlsafe(32)


def create_token(username: str) -> tuple[str, int]:
    expires_in = settings.jwt_expire_minutes * 60
    payload = {
        "sub": username,
        "exp": datetime.now(UTC) + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, jwt_secret(), algorithm=ALGORITHM), expires_in


def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token, jwt_secret(), algorithms=[ALGORITHM], options={"require": ["exp"]}
        )
    except jwt.InvalidTokenError:
        return None
    subject = payload.get("sub")
    return subject if isinstance(subject, str) else None


DOWNLOAD_TOKEN_TYPE = "download"


def create_download_token(path: str, download_name: str, expires_in: int) -> str:
    """Token de un solo archivo para el almacenamiento local. No tiene `sub`, así que
    decode_token lo rechaza: no sirve como sesión."""
    payload = {
        "typ": DOWNLOAD_TOKEN_TYPE,
        "path": path,
        "name": download_name,
        "exp": datetime.now(UTC) + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, jwt_secret(), algorithm=ALGORITHM)


def decode_download_token(token: str) -> tuple[str, str] | None:
    """(ruta, nombre de descarga) si el token es válido, no expiró y es de descarga."""
    try:
        payload = jwt.decode(
            token, jwt_secret(), algorithms=[ALGORITHM], options={"require": ["exp"]}
        )
    except jwt.InvalidTokenError:
        return None
    path, name = payload.get("path"), payload.get("name")
    if payload.get("typ") != DOWNLOAD_TOKEN_TYPE or not isinstance(path, str):
        return None
    return path, name if isinstance(name, str) else "archivo.csv"

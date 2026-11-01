import logging
import secrets
from datetime import UTC, datetime, timedelta
from functools import cache

import jwt

from config.settings import settings

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
ACCESS_TOKEN_TYPE = "access"

@cache
def jwt_secret() -> str:
    if settings.jwt_secret:
        return settings.jwt_secret
    logger.warning("JWT_SECRET no está definido: las sesiones se pierden al reiniciar")
    return secrets.token_urlsafe(32)

def create_token(username: str, version: int) -> tuple[str, int]:
    expires_in = settings.jwt_expire_minutes * 60
    payload = {
        "typ": ACCESS_TOKEN_TYPE,
        "sub": username,
        "ver": version,
        "exp": datetime.now(UTC) + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, jwt_secret(), algorithm=ALGORITHM), expires_in

def decode_token(token: str) -> tuple[str, int] | None:
    """Devuelve (usuario, versión) si el token de sesión es válido"""
    try:
        payload = jwt.decode(
            token, jwt_secret(), algorithms=[ALGORITHM], options={"require": ["exp"]}
        )
    except jwt.InvalidTokenError:
        return None
    # Los tokens de antes no traen typ; los de descarga traen otro y no valen aquí
    if payload.get("typ", ACCESS_TOKEN_TYPE) != ACCESS_TOKEN_TYPE:
        return None
    subject, version = payload.get("sub"), payload.get("ver", 0)
    if not isinstance(subject, str) or not isinstance(version, int):
        return None
    return subject, version

DOWNLOAD_TOKEN_TYPE = "download"

def create_download_token(path: str, download_name: str, expires_in: int) -> str:
    """Token para descargar un archivo del disco. No sirve para iniciar sesión"""
    payload = {
        "typ": DOWNLOAD_TOKEN_TYPE,
        "path": path,
        "name": download_name,
        "exp": datetime.now(UTC) + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, jwt_secret(), algorithm=ALGORITHM)

def decode_download_token(token: str) -> tuple[str, str] | None:
    """Devuelve (ruta, nombre) si el token de descarga es válido y no venció"""
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
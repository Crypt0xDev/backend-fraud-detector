import hashlib
import hmac
import secrets

SCRYPT_PARAMS = {"n": 2**14, "r": 8, "p": 1}
MIN_PASSWORD_LENGTH = 8


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, **SCRYPT_PARAMS)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt, digest = stored.split("$")
        candidate = hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(salt), **SCRYPT_PARAMS
        )
    except ValueError:
        return False
    return hmac.compare_digest(candidate.hex(), digest)


DUMMY_HASH = hash_password(secrets.token_urlsafe(16))

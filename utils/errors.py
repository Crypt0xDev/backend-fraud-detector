"""Errores de los casos de uso. No dependen de HTTP: main.py los convierte en respuestas"""

from collections.abc import Sequence
from typing import Any


class DomainError(Exception):
    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class NotFoundError(DomainError):
    """No existe o el usuario no lo puede ver"""


class ConflictError(DomainError):
    """Choca con el estado actual: repetido, en uso o el último root"""


class ForbiddenError(DomainError):
    """El usuario no puede hacer esto"""


class InvalidRequestError(DomainError):
    """Datos enviados que no sirven, como roles o permisos que no existen"""


class InvalidDataError(DomainError):
    """Datos con un formato que no se puede procesar, como un CSV roto"""


class InvalidRowsError(DomainError):
    """Filas que no pasan la validación; errors tiene el detalle de cada una"""

    def __init__(self, errors: Sequence[Any]):
        super().__init__("Hay filas que no son válidas")
        self.errors = errors


class AuthenticationError(DomainError):
    """Credenciales incorrectas"""


class RateLimitedError(DomainError):
    """Demasiadas peticiones; se puede reintentar en retry_after segundos"""

    def __init__(self, detail: str, retry_after: int):
        super().__init__(detail)
        self.retry_after = retry_after


class UnavailableError(DomainError):
    """Falta algo para atender la petición, como un artefacto del modelo"""

    def __init__(self, detail: str, retry_after: int | None = None):
        super().__init__(detail)
        self.retry_after = retry_after


class StorageFailureError(DomainError):
    """El almacenamiento de archivos no respondió"""

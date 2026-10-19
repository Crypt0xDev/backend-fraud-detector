from typing import Any

from utils.errors import UnavailableError


def unavailable(what: str) -> UnavailableError:
    return UnavailableError(
        f"{what} no está disponible: copia los artefactos del entrenamiento"
    )


def execute(profile: Any) -> Any:
    if profile is None:
        raise unavailable("El perfil del dataset")
    return profile

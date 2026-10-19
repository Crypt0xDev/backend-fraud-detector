from typing import Any

from fastapi import HTTPException, status


def unavailable(what: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"{what} no está disponible: copia los artefactos del entrenamiento",
    )


def execute(profile: Any) -> Any:
    if profile is None:
        raise unavailable("El perfil del dataset")
    return profile

from typing import Any

from fastapi import HTTPException, status

from app.model.model_schema import ExperimentsOut


def execute(experiments: dict | None, metrics: Any):
    """Lista de los modelos que se probaron, para compararlos"""
    if experiments is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Los experimentos no están disponibles"
        )
    deployed = getattr(metrics, "version", None) if metrics is not None else None
    return ExperimentsOut.model_validate({**experiments, "deployed": deployed})

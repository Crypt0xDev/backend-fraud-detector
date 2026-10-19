from typing import Any

from fastapi import HTTPException, Request, status

from app.prediction.prediction_policy import RiskPolicy


def get_model(request: Request) -> Any:
    model = request.app.state.model
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El modelo no está disponible",
        )
    return model


def get_policy(request: Request) -> RiskPolicy:
    return request.app.state.policy


def model_version(request: Request) -> str | None:
    metrics = request.app.state.metrics
    return getattr(metrics, "version", None) if metrics is not None else None

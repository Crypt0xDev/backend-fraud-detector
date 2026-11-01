from typing import Any

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.prediction.prediction_policy import RiskPolicy, current_policy
from config.database import get_db


def get_model(request: Request) -> Any:
    model = request.app.state.model
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El modelo no está disponible",
        )
    return model


def get_base_policy(request: Request) -> RiskPolicy:
    """Umbrales del entrenamiento o de FRAUD_THRESHOLD, sin los ajustes de la web"""
    return request.app.state.policy


def get_policy(request: Request, db: Session = Depends(get_db)) -> RiskPolicy:
    return current_policy(db, get_base_policy(request))


def model_version(request: Request) -> str | None:
    metrics = request.app.state.metrics
    return getattr(metrics, "version", None) if metrics is not None else None

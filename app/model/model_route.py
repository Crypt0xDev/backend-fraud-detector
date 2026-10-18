from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.model.model_schema import (
    ExperimentOut,
    ExperimentsOut,
    HealthOut,
    MetricsOut,
    ModelInfoOut,
)
from config.settings import settings
from utils.auth import get_current_user

router = APIRouter(tags=["model"])


@router.get("/health", response_model=HealthOut)
def health(request: Request) -> HealthOut:
    return HealthOut(
        status="ok",
        model_loaded=request.app.state.model is not None,
        metrics_loaded=request.app.state.metrics is not None,
    )


@router.get(
    "/metrics",
    response_model=MetricsOut,
    response_model_exclude_none=True,
    dependencies=[Depends(get_current_user)],
)
def metrics(request: Request) -> MetricsOut:
    metrics = request.app.state.metrics
    if metrics is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Las métricas no están disponibles",
        )
    return metrics


@router.get(
    "/model/info", response_model=ModelInfoOut, dependencies=[Depends(get_current_user)]
)
def model_info(request: Request) -> ModelInfoOut:
    """Versión, variables y política de decisión del modelo cargado."""
    info = request.app.state.metrics.model_dump() if request.app.state.metrics else {}
    policy = request.app.state.policy
    return ModelInfoOut(
        loaded=request.app.state.model is not None,
        version=info.get("version"),
        model_name=info.get("model_name"),
        model_type=info.get("model_type"),
        feature_set=info.get("feature_set"),
        feature_set_label=info.get("feature_set_label"),
        features=info.get("features") or [],
        trained_at=info.get("trained_at"),
        split=info.get("split"),
        threshold=policy.high,
        risk_levels={
            "medium": policy.medium,
            "high": policy.high,
            "source": policy.source,
        },
        threshold_criterion=info.get("threshold_criterion"),
        sha256=info.get("sha256"),
        limits={
            "max_batch_rows": settings.max_batch_rows,
            "max_upload_mb": settings.max_upload_mb,
            "rate_limit_per_minute": settings.rate_limit_per_minute,
        },
    )


def get_experiments(request: Request) -> ExperimentsOut:
    data = request.app.state.experiments
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Los experimentos no están disponibles",
        )
    metrics = request.app.state.metrics
    deployed = getattr(metrics, "version", None) if metrics is not None else None
    return ExperimentsOut.model_validate({**data, "deployed": deployed})


@router.get(
    "/experiments",
    response_model=ExperimentsOut,
    dependencies=[Depends(get_current_user)],
)
def experiments(request: Request) -> ExperimentsOut:
    """Comparación de modelos y conjuntos de variables con la misma partición temporal."""
    return get_experiments(request)


@router.get(
    "/experiments/{version}",
    response_model=ExperimentOut,
    dependencies=[Depends(get_current_user)],
)
def experiment(version: str, request: Request) -> ExperimentOut:
    found = next(
        (e for e in get_experiments(request).experiments if e.version == version), None
    )
    if found is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="El experimento no existe"
        )
    return found

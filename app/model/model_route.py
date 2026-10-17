from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.model.model_schema import HealthOut, MetricsOut
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

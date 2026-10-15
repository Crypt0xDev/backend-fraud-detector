from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from app.model_info.schemas import HealthOut

router = APIRouter(tags=["model"])


@router.get("/health", response_model=HealthOut)
def health(request: Request) -> HealthOut:
    return HealthOut(
        status="ok",
        model_loaded=request.app.state.model is not None,
        metrics_loaded=request.app.state.metrics is not None,
    )


@router.get("/metrics")
def metrics(request: Request) -> dict[str, Any]:
    metrics = request.app.state.metrics
    if metrics is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Las métricas no están disponibles",
        )
    return metrics

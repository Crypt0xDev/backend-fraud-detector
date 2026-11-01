from fastapi import HTTPException, status

from app.model.model_schema import MetricsOut


def execute(metrics: MetricsOut | None):
    if metrics is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Las métricas no están disponibles"
        )
    return metrics

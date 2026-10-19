from typing import Any

from app.model.model_schema import HealthOut


def execute(model: Any, metrics: Any) -> HealthOut:
    return HealthOut(
        status="ok",
        model_loaded=model is not None,
        metrics_loaded=metrics is not None,
    )

from typing import Any

from app.model.model_schema import HealthOut
from config import database


def execute(model: Any, metrics: Any) -> HealthOut:
    database_ok = database.check_database()
    healthy = model is not None and database_ok is not False
    return HealthOut(
        status="ok" if healthy else "degraded",
        model_loaded=model is not None,
        metrics_loaded=metrics is not None,
        database_ok=database_ok,
    )

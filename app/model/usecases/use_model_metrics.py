from app.model.model_schema import MetricsOut
from utils.errors import UnavailableError


def execute(metrics: MetricsOut | None) -> MetricsOut:
    if metrics is None:
        raise UnavailableError("Las métricas no están disponibles")
    return metrics

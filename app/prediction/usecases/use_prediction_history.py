import logging

from app.prediction.prediction_repository import PredictionRepository
from app.prediction.prediction_schema import (
    PredictionHistoryOut,
    PredictOut,
    Transaction,
)

logger = logging.getLogger(__name__)


def save_predictions(
    predictions: PredictionRepository | None,
    username: str,
    transactions: list[Transaction],
    result: PredictOut,
) -> None:
    """Guarda el análisis en el historial; si falla, la predicción se devuelve igual."""
    if predictions is None:
        return
    try:
        predictions.add_many(
            username, transactions, result.predictions, result.threshold
        )
    except Exception:
        logger.exception("No se pudo guardar el historial de predicciones")


def prediction_history(
    predictions: PredictionRepository,
    owner: str | None,
    limit: int,
    offset: int = 0,
    alerts_only: bool = False,
) -> PredictionHistoryOut:
    total, flagged = predictions.totals(owner)
    return PredictionHistoryOut(
        total=total,
        flagged=flagged,
        items=predictions.recent(owner, limit, offset, alerts_only),
    )

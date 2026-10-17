from typing import Any

from app.prediction.prediction_features import DEFAULT_COLUMNS, build_features
from app.prediction.prediction_schema import Prediction, PredictOut, Transaction
from config.settings import settings


def predict(
    model: Any, transactions: list[Transaction], threshold: float
) -> list[Prediction]:
    frame = build_features(transactions)
    columns = getattr(model, "feature_names_in_", None)
    frame = frame[list(columns) if columns is not None else DEFAULT_COLUMNS]

    probabilities = model.predict_proba(frame)[:, 1]
    return [
        Prediction(fraud_probability=float(p), is_fraud=bool(p >= threshold))
        for p in probabilities
    ]


def predict_transactions(model: Any, transactions: list[Transaction]) -> PredictOut:
    threshold = settings.fraud_threshold
    return PredictOut(
        threshold=threshold, predictions=predict(model, transactions, threshold)
    )

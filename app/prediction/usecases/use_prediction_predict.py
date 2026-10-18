from typing import Any

from app.prediction.prediction_features import DEFAULT_COLUMNS, build_features
from app.prediction.prediction_policy import RiskPolicy
from app.prediction.prediction_schema import (
    Contribution,
    Prediction,
    PredictOut,
    RiskLevelsOut,
    Transaction,
)
from utils.explain import explain as explain_rows

MAX_EXPLAINED = 10


def predict(
    model: Any,
    transactions: list[Transaction],
    policy: RiskPolicy,
    with_explanation: bool = False,
) -> list[Prediction]:
    frame = build_features(transactions)
    columns = getattr(model, "feature_names_in_", None)
    probabilities = model.predict_proba(
        frame[list(columns) if columns is not None else DEFAULT_COLUMNS]
    )[:, 1]
    explanations = (
        explain_rows(model, frame)
        if with_explanation and len(transactions) <= MAX_EXPLAINED
        else None
    )
    return [
        Prediction(
            fraud_probability=float(p),
            is_fraud=bool(p >= policy.high),
            risk_level=policy.level(float(p)),
            explanation=(
                [Contribution(**c) for c in explanations[i]] if explanations else None
            ),
        )
        for i, p in enumerate(probabilities)
    ]


def predict_transactions(
    model: Any,
    transactions: list[Transaction],
    policy: RiskPolicy,
    *,
    with_explanation: bool = False,
    model_version: str | None = None,
) -> PredictOut:
    return PredictOut(
        threshold=policy.high,
        predictions=predict(model, transactions, policy, with_explanation),
        risk_levels=RiskLevelsOut(
            medium=policy.medium, high=policy.high, source=policy.source
        ),
        model_version=model_version,
    )

import logging
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.prediction.prediction_entity import PredictionRecord
from app.prediction.prediction_features import DEFAULT_COLUMNS, build_features
from app.prediction.prediction_policy import RiskPolicy
from app.prediction.prediction_schema import (
    Contribution,
    Prediction,
    PredictOut,
    RiskLevelsOut,
    Transaction,
)
from app.user.user_entity import User
from utils.explain import explain as explain_rows

logger = logging.getLogger(__name__)

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


def save_history(
    db: Session, username: str, transactions: list[Transaction], result: PredictOut
) -> None:
    """Guarda el análisis en el historial. Si falla, igual se devuelve el resultado"""
    try:
        db.add_all(
            PredictionRecord(
                id=uuid4(),
                username=username,
                type=t.type,
                amount=t.amount,
                name_orig=t.nameOrig,
                name_dest=t.nameDest,
                fraud_probability=p.fraud_probability,
                is_fraud=p.is_fraud,
                threshold=result.threshold,
                model_version=result.model_version,
            )
            for t, p in zip(transactions, result.predictions, strict=True)
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("No se pudo guardar el historial de predicciones")


def execute(
    db: Session,
    current_user: User,
    model: Any,
    policy: RiskPolicy,
    transactions: list[Transaction],
    *,
    explain: bool = False,
    model_version: str | None = None,
) -> PredictOut:
    result = predict_transactions(
        model,
        transactions,
        policy,
        with_explanation=explain,
        model_version=model_version,
    )
    save_history(db, current_user.username, transactions, result)
    return result

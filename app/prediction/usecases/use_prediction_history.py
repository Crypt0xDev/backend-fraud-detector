from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.auth_dependency import is_root
from app.prediction.prediction_entity import PredictionRecord
from app.prediction.prediction_schema import PredictionHistoryOut, PredictionRecordOut
from app.user.user_entity import User
from utils.errors import ForbiddenError


def execute(
    db: Session,
    current_user: User,
    all: bool,
    limit: int,
    offset: int = 0,
    alerts_only: bool = False,
) -> PredictionHistoryOut:
    """Últimas transacciones analizadas; con `all` el root ve las de todos"""
    if all and not is_root(current_user):
        raise ForbiddenError(
            "Solo un administrador puede ver las predicciones de todos"
        )
    owner = [] if all else [PredictionRecord.username == current_user.username]

    total, flagged = (
        db.query(
            func.count(PredictionRecord.id),
            func.count(PredictionRecord.id).filter(PredictionRecord.is_fraud),
        )
        .filter(*owner)
        .one()
    )
    query = db.query(PredictionRecord).filter(*owner)
    if alerts_only:
        query = query.filter(PredictionRecord.is_fraud)
    items = (
        query.order_by(PredictionRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return PredictionHistoryOut(
        total=total,
        flagged=flagged,
        items=[
            PredictionRecordOut.model_validate(p, from_attributes=True) for p in items
        ],
    )

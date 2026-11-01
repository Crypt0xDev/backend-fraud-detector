from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.auth_dependency import is_root
from app.prediction.prediction_entity import PredictionRecord
from app.prediction.prediction_schema import PredictionHistoryOut, PredictionRecordOut
from app.user.user_entity import User


def execute(db: Session, current_user: User, all: bool, page: int, page_size: int, alerts_only: bool = False) -> PredictionHistoryOut:
    """Últimas transacciones analizadas; con `all` el root ve las de todos"""
    # Verificar permisos del usuario
    if all and not is_root(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un administrador puede ver las predicciones de todos"
        )
    owner = [] if all else [PredictionRecord.username == current_user.username]

    total, flagged = db.execute(
        select(
            func.count(PredictionRecord.id),
            func.count(PredictionRecord.id).filter(PredictionRecord.is_fraud),
        )
        .where(*owner)
    ).one()
    query = select(PredictionRecord).where(*owner)
    if alerts_only:
        query = query.where(PredictionRecord.is_fraud)
    items = db.scalars(
        query.order_by(PredictionRecord.created_at.desc(), PredictionRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return PredictionHistoryOut(
        total=total,
        flagged=flagged,
        page=page,
        page_size=page_size,
        items=[
            PredictionRecordOut.model_validate(p, from_attributes=True) for p in items
        ],
    )

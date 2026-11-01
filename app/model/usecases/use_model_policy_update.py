import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.model.model_schema import PolicyIn, PolicyOut
from app.model.usecases.use_model_policy_view import execute as view_policy_execute
from app.prediction.prediction_entity import PredictionPolicy
from app.prediction.prediction_policy import POLICY_ID, RiskPolicy
from app.user.user_entity import User
from utils.helpers import utcnow

logger = logging.getLogger(__name__)

def save(db: Session, current_user: User, payload: PolicyIn) -> None:
    row = db.get(PredictionPolicy, POLICY_ID) or PredictionPolicy(id=POLICY_ID)
    row.medium = payload.medium
    row.high = payload.high
    row.updated_by = current_user.username
    row.updated_at = utcnow()
    db.add(row)
    db.commit()

def execute(db: Session, current_user: User, base: RiskPolicy, payload: PolicyIn) -> PolicyOut:
    """Guarda los umbrales; las predicciones siguientes ya los usan"""
    try:
        save(db, current_user, payload)
    except IntegrityError:
        # Otra petición creó la fila a la vez: se vuelve a intentar actualizándola
        db.rollback()
        save(db, current_user, payload)
    logger.info(
        "Umbrales cambiados por %s: medio %s, alerta %s",
        current_user.username, payload.medium, payload.high,
    )
    return view_policy_execute(db=db, base=base)

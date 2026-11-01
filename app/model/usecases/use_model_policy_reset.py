import logging

from sqlalchemy.orm import Session

from app.model.model_schema import PolicyOut
from app.model.usecases.use_model_policy_view import execute as view_policy_execute
from app.prediction.prediction_entity import PredictionPolicy
from app.prediction.prediction_policy import POLICY_ID, RiskPolicy
from app.user.user_entity import User

logger = logging.getLogger(__name__)

def execute(db: Session, current_user: User, base: RiskPolicy) -> PolicyOut:
    """Vuelve a los umbrales del entrenamiento (o de FRAUD_THRESHOLD)"""
    row = db.get(PredictionPolicy, POLICY_ID)
    if row is not None:
        db.delete(row)
        db.commit()
        logger.info("Umbrales restablecidos por %s", current_user.username)
    return view_policy_execute(db=db, base=base)

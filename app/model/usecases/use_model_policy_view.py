from sqlalchemy.orm import Session

from app.model.model_schema import PolicyLevelsOut, PolicyOut
from app.prediction.prediction_entity import PredictionPolicy
from app.prediction.prediction_policy import POLICY_ID, RiskPolicy, current_policy

def levels(policy: RiskPolicy) -> PolicyLevelsOut:
    return PolicyLevelsOut(medium=policy.medium, high=policy.high, source=policy.source)

def execute(db: Session, base: RiskPolicy) -> PolicyOut:
    """Umbrales en uso y los del entrenamiento"""
    row = db.get(PredictionPolicy, POLICY_ID)
    return PolicyOut(
        **levels(current_policy(db, base)).model_dump(),
        default=levels(base),
        updated_by=row.updated_by if row else None,
        updated_at=row.updated_at if row else None,
    )

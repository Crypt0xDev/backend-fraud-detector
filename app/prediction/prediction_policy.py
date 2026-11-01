from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.prediction.prediction_entity import PredictionPolicy

RiskLevel = Literal["low", "medium", "high"]
DEFAULT_THRESHOLD = 0.5


@dataclass(frozen=True)
class RiskPolicy:
    """Umbrales del score: desde high es alerta y desde medium hay que revisarla"""

    medium: float
    high: float
    source: str

    def level(self, score: float) -> RiskLevel:
        if score >= self.high:
            return "high"
        return "medium" if score >= self.medium else "low"


def build_policy(metrics: Any, override: float | None) -> RiskPolicy:
    """Toma los umbrales de metrics.json, o FRAUD_THRESHOLD si está definido"""
    info = metrics.model_dump() if metrics is not None else {}
    levels = info.get("risk_levels") or {}
    trained = levels.get("high", info.get("threshold"))
    if override is not None:
        high, source = override, "FRAUD_THRESHOLD"
    elif trained is not None:
        high, source = float(trained), "metrics.json"
    else:
        high, source = DEFAULT_THRESHOLD, "por defecto"
    medium = min(float(levels.get("medium", high)), high)
    return RiskPolicy(medium=medium, high=high, source=source)

WEB_SOURCE = "web"
POLICY_ID = 1


def current_policy(db: Session, base: RiskPolicy) -> RiskPolicy:
    """Los umbrales ajustados en la web; si no hay, los del arranque (base).
    Se leen en cada petición para que todos los workers usen los mismos"""
    row = db.get(PredictionPolicy, POLICY_ID)
    if row is None:
        return base
    return RiskPolicy(medium=row.medium, high=row.high, source=WEB_SOURCE)

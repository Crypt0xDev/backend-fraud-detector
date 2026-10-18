from dataclasses import dataclass
from typing import Any, Literal

RiskLevel = Literal["low", "medium", "high"]
DEFAULT_THRESHOLD = 0.5


@dataclass(frozen=True)
class RiskPolicy:
    """Política de decisión: score >= high genera alerta; medium marca revisión."""

    medium: float
    high: float
    source: str

    def level(self, score: float) -> RiskLevel:
        if score >= self.high:
            return "high"
        return "medium" if score >= self.medium else "low"


def build_policy(metrics: Any, override: float | None) -> RiskPolicy:
    """Umbrales elegidos en validación (metrics.json); FRAUD_THRESHOLD los fuerza."""
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

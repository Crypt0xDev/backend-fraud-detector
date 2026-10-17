from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Score = float | None


class HealthOut(BaseModel):
    status: Literal["ok"]
    model_loaded: bool
    metrics_loaded: bool


class MetricsOut(BaseModel):
    """Métricas del entrenamiento; las claves extra de metrics.json se devuelven tal cual."""

    model_config = ConfigDict(extra="allow")

    model_name: str | None = None
    trained_at: str | None = None
    threshold: float | None = Field(default=None, ge=0, le=1)
    roc_auc: Score = None
    pr_auc: Score = None
    precision: Score = None
    recall: Score = None
    f1: Score = None
    accuracy: Score = None
    # Formato de sklearn: [[tn, fp], [fn, tp]]
    confusion_matrix: tuple[tuple[int, int], tuple[int, int]] | None = None

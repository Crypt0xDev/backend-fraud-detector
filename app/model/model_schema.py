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


class ModelInfoOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    loaded: bool
    version: str | None = None
    model_name: str | None = None
    model_type: str | None = None
    feature_set: str | None = None
    feature_set_label: str | None = None
    features: list[str] = []
    trained_at: str | None = None
    split: str | None = None
    threshold: float
    risk_levels: dict[str, float | str]
    threshold_criterion: str | None = None
    sha256: str | None = None
    limits: dict[str, int]


class ExperimentOut(BaseModel):
    """Fila de experiments.json; las claves extra se devuelven tal cual."""

    model_config = ConfigDict(extra="allow", protected_namespaces=())

    version: str
    model_name: str
    model_type: str
    feature_set: str
    val_pr_auc: float
    pr_auc: float


class ExperimentsOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    created_at: str | None = None
    split: str | None = None
    selection_criterion: str | None = None
    recommended: str | None = None
    deployed: str | None = None
    experiments: list[ExperimentOut]

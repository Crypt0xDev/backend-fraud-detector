# python
from datetime import datetime
from typing import Literal, Self

# pydantic
from pydantic import BaseModel, ConfigDict, Field, model_validator

# dependencias
from utils.schemas import BaseSchema

Score = float | None

# Inicio del response del estado
class HealthOut(BaseModel):
    # degraded: falta el modelo o la base no responde
    status: Literal["ok", "degraded"]
    model_loaded: bool
    metrics_loaded: bool
    # None si no hay DATABASE_URL
    database_ok: bool | None = None
# Fin del response del estado


# Inicio del response de las métricas
class PrPointOut(BaseModel):
    threshold: float
    precision: float
    recall: float


class MetricsOut(BaseModel):
    """Métricas del entrenamiento. Si metrics.json trae más datos, se devuelven igual"""

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
    pr_curve: list[PrPointOut] | None = None
# Fin del response de las métricas


# Inicio del response de la información del modelo
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
# Fin del response de la información del modelo


# Inicio del response de los experimentos
class ExperimentOut(BaseModel):
    """Un experimento de experiments.json. Si trae más datos, se devuelven igual"""

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
# Fin del response de los experimentos


# Inicio de la política de decisión
class PolicyIn(BaseSchema):
    """Umbrales del score: desde high es alerta y desde medium hay que revisarla"""

    medium: float = Field(ge=0, le=1)
    high: float = Field(gt=0, le=1)

    @model_validator(mode="after")
    def check_order(self) -> Self:
        if self.medium > self.high:
            raise ValueError("El umbral de riesgo medio no puede superar al de alerta")
        return self


class PolicyLevelsOut(BaseModel):
    medium: float
    high: float
    source: str


class PolicyOut(PolicyLevelsOut):
    # Los del entrenamiento o FRAUD_THRESHOLD, para poder volver a ellos
    default: PolicyLevelsOut
    updated_by: str | None = None
    updated_at: datetime | None = None
# Fin de la política de decisión

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.prediction.prediction_schema import TransactionType


class SamplePointOut(BaseModel):
    step: int
    type: TransactionType
    amount: float
    oldbalanceOrg: float
    oldbalanceDest: float
    # Etiqueta real del dataset (isFraud), predicción (alert) y score: no se mezclan
    label: Literal[0, 1]
    alert: Literal[0, 1]
    score: float
    pc1: float
    pc2: float
    pc3: float


class SampleOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    total_in_sample: int
    matched: int
    returned: int
    meta: dict[str, Any]
    points: list[SamplePointOut]


class DatasetProfileOut(BaseModel):
    """Perfil del CSV de PaySim generado por ml-fraud-training/profile_data.py."""

    model_config = ConfigDict(extra="allow")

    rows: int

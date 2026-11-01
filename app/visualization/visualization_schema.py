# python
from typing import Any, Literal

# pydantic
from pydantic import BaseModel, ConfigDict

# esquemas
from app.prediction.prediction_schema import TransactionType


class SamplePointOut(BaseModel):
    step: int
    type: TransactionType
    amount: float
    oldbalanceOrg: float
    oldbalanceDest: float
    # isFraud es lo real del dataset; alert y score son lo que dice el modelo
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
    """Resumen del CSV de PaySim, sale de ml-fraud-training/profile_data.py"""

    model_config = ConfigDict(extra="allow")

    rows: int

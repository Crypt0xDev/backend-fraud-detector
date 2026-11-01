# python
from datetime import datetime
from typing import Literal
from uuid import UUID

# pydantic
from pydantic import BaseModel, ConfigDict, Field

# dependencias
from config.settings import settings
from app.prediction.prediction_policy import RiskLevel

TransactionType = Literal["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]

# En PaySim miden 11 caracteres; se guardan en el historial
MAX_NAME_LENGTH = 100


# Inicio del registro de una predicción
class Transaction(BaseModel):
    """Una transacción con las columnas de PaySim"""

    # Sin Infinity ni NaN: no son montos y se guardarían en el historial
    model_config = ConfigDict(allow_inf_nan=False)

    step: int = Field(ge=0)
    type: TransactionType
    amount: float = Field(ge=0)
    nameOrig: str | None = Field(default=None, max_length=MAX_NAME_LENGTH)
    oldbalanceOrg: float = Field(ge=0)
    newbalanceOrig: float = Field(ge=0)
    nameDest: str | None = Field(default=None, max_length=MAX_NAME_LENGTH)
    oldbalanceDest: float = Field(ge=0)
    newbalanceDest: float = Field(ge=0)


class PredictIn(BaseModel):
    transactions: list[Transaction] = Field(
        min_length=1, max_length=settings.max_predict_rows
    )
# Fin del registro de una predicción


# Inicio del response de la predicción
class Contribution(BaseModel):
    """Cuánto sube o baja una variable el score (no es la causa del fraude)"""

    feature: str
    value: float | str
    contribution: float


class Prediction(BaseModel):
    fraud_probability: float
    # Es una alerta del modelo, no un fraude confirmado
    is_fraud: bool
    risk_level: RiskLevel = "low"
    explanation: list[Contribution] | None = None


class RiskLevelsOut(BaseModel):
    medium: float
    high: float
    source: str


class PredictOut(BaseModel):
    threshold: float
    predictions: list[Prediction]
    batch_id: UUID | None = None
    risk_levels: RiskLevelsOut | None = None
    model_version: str | None = None
# Fin del response de la predicción


# Inicio del response del historial
class PredictionRecordOut(BaseModel):
    id: UUID
    username: str
    type: str
    amount: float
    name_orig: str | None = None
    name_dest: str | None = None
    fraud_probability: float
    is_fraud: bool
    threshold: float
    model_version: str | None = None
    created_at: datetime


class PredictionHistoryOut(BaseModel):
    # total y flagged cuentan todo el historial, aunque se pida alerts_only
    total: int
    flagged: int
    page: int
    page_size: int
    items: list[PredictionRecordOut]
# Fin del response del historial

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.prediction.prediction_policy import RiskLevel
from config.settings import settings

TransactionType = Literal["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]


class Transaction(BaseModel):
    """Transacción con las columnas originales de PaySim (sin las etiquetas)."""

    step: int = Field(ge=0)
    type: TransactionType
    amount: float = Field(ge=0)
    nameOrig: str | None = None
    oldbalanceOrg: float = Field(ge=0)
    newbalanceOrig: float = Field(ge=0)
    nameDest: str | None = None
    oldbalanceDest: float = Field(ge=0)
    newbalanceDest: float = Field(ge=0)


class PredictIn(BaseModel):
    transactions: list[Transaction] = Field(
        min_length=1, max_length=settings.max_batch_rows
    )


class Contribution(BaseModel):
    """Aporte de una variable al score (escala log-odds para árboles y regresión
    logística). Positivo empuja hacia alerta; no implica causalidad."""

    feature: str
    value: float | str
    contribution: float


class Prediction(BaseModel):
    fraud_probability: float
    # Alerta del modelo (score >= umbral), no un fraude confirmado
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
    created_at: datetime


class PredictionHistoryOut(BaseModel):
    total: int
    flagged: int
    items: list[PredictionRecordOut]

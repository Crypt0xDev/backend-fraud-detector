from typing import Literal

from pydantic import BaseModel, Field

from app.shared.config import settings

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


class Prediction(BaseModel):
    fraud_probability: float
    is_fraud: bool


class PredictOut(BaseModel):
    threshold: float
    predictions: list[Prediction]

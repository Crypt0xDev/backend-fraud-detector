from typing import IO, Any

import pandas as pd
from pydantic import TypeAdapter

from app.prediction.schemas import Prediction, Transaction

transactions_adapter = TypeAdapter(list[Transaction])


class InvalidCSVError(ValueError):
    pass


def predict(
    model: Any, transactions: list[Transaction], threshold: float
) -> list[Prediction]:
    frame = pd.DataFrame([transaction.model_dump() for transaction in transactions])
    columns = getattr(model, "feature_names_in_", None)
    if columns is not None:
        frame = frame[list(columns)]

    probabilities = model.predict_proba(frame)[:, 1]
    return [
        Prediction(fraud_probability=float(p), is_fraud=bool(p >= threshold))
        for p in probabilities
    ]


def read_csv(file: IO[bytes], max_rows: int) -> list[Transaction]:
    """Lee un CSV de PaySim; las columnas extra (p. ej. isFraud) se ignoran."""
    try:
        frame = pd.read_csv(file, nrows=max_rows + 1)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as e:
        raise InvalidCSVError(f"No se pudo leer el CSV: {e}") from e

    if frame.empty:
        raise InvalidCSVError("El CSV no tiene filas")
    if len(frame) > max_rows:
        raise InvalidCSVError(f"El CSV supera el máximo de {max_rows} filas")

    rows = frame.astype(object).where(frame.notna(), None).to_dict("records")
    return transactions_adapter.validate_python(rows)

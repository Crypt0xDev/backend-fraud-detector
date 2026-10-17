import io
from typing import IO, Any

import pandas as pd
from pydantic import TypeAdapter

from app.batch.batch_repository import BatchRepository
from app.batch.usecases.use_batch_save import save_batch
from app.prediction.prediction_schema import Prediction, PredictOut, Transaction
from app.prediction.usecases.use_prediction_predict import predict_transactions
from config.settings import settings
from utils.storage import SupabaseStorage

transactions_adapter = TypeAdapter(list[Transaction])


class InvalidCSVError(ValueError):
    pass


def read_csv(file: IO[bytes], max_rows: int) -> tuple[pd.DataFrame, list[Transaction]]:
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
    return frame, transactions_adapter.validate_python(rows)


def predictions_csv(frame: pd.DataFrame, predictions: list[Prediction]) -> bytes:
    return (
        frame.assign(
            fraud_probability=[p.fraud_probability for p in predictions],
            is_fraud=[p.is_fraud for p in predictions],
        )
        .to_csv(index=False)
        .encode()
    )


def predict_csv_file(
    model: Any,
    original: bytes,
    *,
    file_name: str,
    username: str,
    storage: SupabaseStorage | None,
    batches: BatchRepository | None,
) -> PredictOut:
    """Predice el CSV y, si hay Storage y base de datos, lo guarda en el historial."""
    frame, transactions = read_csv(io.BytesIO(original), settings.max_batch_rows)
    result = predict_transactions(model, transactions)
    if storage is not None and batches is not None:
        result.batch_id = save_batch(
            storage,
            batches,
            username=username,
            file_name=file_name,
            original=original,
            predictions=predictions_csv(frame, result.predictions),
            flagged_rows=sum(p.is_fraud for p in result.predictions),
            total_rows=len(result.predictions),
            threshold=result.threshold,
        )
    return result

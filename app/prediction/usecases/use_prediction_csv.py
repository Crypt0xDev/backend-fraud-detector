import io
from typing import IO, Any, cast

import pandas as pd
from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from app.prediction.prediction_policy import RiskPolicy
from app.prediction.prediction_port import BatchArchive
from app.prediction.prediction_schema import Prediction, PredictOut, Transaction
from app.prediction.usecases.use_prediction_predict import predict_transactions
from app.user.user_entity import User
from config.error_handlers import json_safe

transactions_adapter = TypeAdapter(list[Transaction])


class InvalidCSVError(ValueError):
    pass


def read_csv(file: IO[bytes], max_rows: int) -> tuple[pd.DataFrame, list[Transaction]]:
    """Lee un CSV de PaySim. Las columnas que sobran, como isFraud, no se usan"""
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


FORMULA_PREFIXES = ("=", "+", "-", "@", chr(9), chr(13))


def escape_formula(value: Any) -> Any:
    """Evita que Excel o Sheets tomen un texto del CSV como fórmula"""
    if isinstance(value, str) and value.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


def safe_csv(frame: pd.DataFrame) -> bytes:
    text_columns = frame.select_dtypes(include=["object", "string"]).columns
    escaped = frame.assign(**{c: frame[c].map(escape_formula) for c in text_columns})
    return escaped.to_csv(index=False).encode()


def predictions_csv(frame: pd.DataFrame, predictions: list[Prediction]) -> bytes:
    return safe_csv(
        frame.assign(
            fraud_probability=[p.fraud_probability for p in predictions],
            is_fraud=[p.is_fraud for p in predictions],
            risk_level=[p.risk_level for p in predictions],
        )
    )


def execute(
    db: Session,
    current_user: User,
    model: Any,
    policy: RiskPolicy,
    original: bytes,
    *,
    file_name: str,
    max_rows: int,
    archive: BatchArchive | None,
    model_version: str | None = None,
):
    """Analiza el CSV y, si hay almacenamiento, lo guarda en el historial"""
    # Verificar que el CSV se pueda leer y que sus filas sean válidas
    try:
        frame, transactions = read_csv(io.BytesIO(original), max_rows)
    except InvalidCSVError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error)
        ) from error
    except ValidationError as error:
        # El mismo detalle que da FastAPI; json_safe cambia Infinity y NaN por texto
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=json_safe(jsonable_encoder(error.errors(include_url=False, include_context=False)))
        ) from error

    result = predict_transactions(
        model, transactions, policy, model_version=model_version
    )
    if archive is not None:
        result.batch_id = archive.save(
            db,
            username=cast(str, current_user.username),
            file_name=file_name,
            original=original,
            predictions=predictions_csv(frame, result.predictions),
            flagged_rows=sum(p.is_fraud for p in result.predictions),
            total_rows=len(result.predictions),
            threshold=result.threshold,
            model_version=result.model_version,
        )
    return result

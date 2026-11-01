import hashlib
import json
import logging
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import joblib
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_model(
    path: Path,
    expected_sha256: str | None = None,
    available_columns: Iterable[str] | None = None,
    threads: int | None = None,
) -> Any | None:
    if not path.exists():
        logger.warning("No se encontró el modelo en %s", path)
        return None
    if expected_sha256 and file_sha256(path) != expected_sha256.strip().lower():
        logger.error("El hash SHA-256 de %s no coincide con MODEL_SHA256", path)
        return None
    try:
        model = joblib.load(path)
    except Exception:
        logger.exception("No se pudo cargar el modelo desde %s", path)
        return None
    if not hasattr(model, "predict_proba"):
        logger.error("El objeto en %s no tiene predict_proba", path)
        return None

    columns = getattr(model, "feature_names_in_", None)
    if columns is not None and available_columns is not None:
        missing = sorted(set(columns) - set(available_columns))
        if missing:
            logger.error(
                "El modelo espera columnas que la API no recibe: %s",
                ", ".join(missing),
            )
            return None

    if threads is not None:
        limit_threads(model, threads)
    logger.debug("Modelo cargado desde %s", path)
    return model


def limit_threads(model: Any, threads: int) -> None:
    """Limita los núcleos que usa el modelo"""
    if not hasattr(model, "get_params"):
        return
    params = {
        name: threads
        for name in model.get_params()
        if name == "n_jobs" or name.endswith("__n_jobs")
    }
    if params:
        model.set_params(**params)

def load_metrics[T: BaseModel](path: Path, schema: type[T]) -> T | None:
    if not path.exists():
        logger.warning("No se encontraron las métricas en %s", path)
        return None
    try:
        metrics = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("No se pudieron leer las métricas desde %s", path)
        return None
    try:
        return schema.model_validate(metrics)
    except ValidationError as error:
        logger.error("Las métricas en %s no son válidas: %s", path, error)
        return None

def load_json(path: Path) -> Any | None:
    if not path.exists():
        logger.warning("No se encontró %s", path)
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("No se pudo leer %s", path)
        return None

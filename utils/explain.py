"""Aportes por variable de una predicción (TreeSHAP de XGBoost o coeficientes de la
regresión logística). Explican el score del modelo, no prueban un fraude."""

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _original_name(name: str) -> str:
    column = name.split("__", 1)[-1]
    return "type" if column.startswith("type_") else column


def _raw_contributions(estimator: Any, transformed: np.ndarray) -> np.ndarray | None:
    if hasattr(estimator, "get_booster"):
        import xgboost

        matrix = xgboost.DMatrix(transformed)
        return estimator.get_booster().predict(matrix, pred_contribs=True)[:, :-1]
    if hasattr(estimator, "coef_"):
        return transformed * estimator.coef_[0]
    return None


def explain(model: Any, frame: pd.DataFrame) -> list[list[dict]] | None:
    """Lista de aportes por fila, ordenados por magnitud; None si el modelo no los
    soporta (p. ej. Random Forest)."""
    if not hasattr(model, "steps") or len(model.steps) < 2:
        return None
    preprocess, estimator = model[:-1], model[-1]
    try:
        columns = list(model.feature_names_in_)
        transformed = preprocess.transform(frame[columns])
        if hasattr(transformed, "toarray"):
            transformed = transformed.toarray()
        raw = _raw_contributions(estimator, np.asarray(transformed, dtype=float))
        if raw is None:
            return None
        names = [_original_name(n) for n in preprocess.get_feature_names_out()]
    except Exception:
        logger.exception("No se pudo calcular la explicación")
        return None

    result = []
    for row_index, row in enumerate(raw):
        totals: dict[str, float] = {}
        for name, value in zip(names, row, strict=True):
            totals[name] = totals.get(name, 0.0) + float(value)
        original = frame.iloc[row_index]
        result.append(
            [
                {
                    "feature": name,
                    "value": original[name]
                    if name == "type"
                    else float(original[name]),
                    "contribution": round(value, 4),
                }
                for name, value in sorted(totals.items(), key=lambda kv: -abs(kv[1]))
            ]
        )
    return result

import logging
from collections.abc import Hashable
from pathlib import Path

import pandas as pd

from app.visualization.visualization_schema import SampleOut, SamplePointOut

logger = logging.getLogger(__name__)

COLUMNS: dict[Hashable, str] = {
    "step": "int32",
    "type": "string",
    "amount": "float64",
    "oldbalanceOrg": "float64",
    "oldbalanceDest": "float64",
    "isFraud": "int8",
    "alert": "int8",
    "score": "float64",
    "pc1": "float64",
    "pc2": "float64",
    "pc3": "float64",
}


def load_sample(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        logger.debug("No se encontró la muestra de visualización en %s", path)
        return None
    try:
        return pd.read_csv(path, usecols=list(COLUMNS), dtype=COLUMNS)
    except Exception:
        logger.exception("No se pudo leer la muestra %s", path)
        return None


def filter_sample(
    sample: pd.DataFrame,
    meta: dict,
    *,
    types: list[str] | None,
    step_min: int | None,
    step_max: int | None,
    score_min: float,
    score_max: float,
    limit: int,
    seed: int = 42,
) -> SampleOut:
    mask = sample["score"].between(score_min, score_max)
    if types:
        mask &= sample["type"].isin(types)
    if step_min is not None:
        mask &= sample["step"] >= step_min
    if step_max is not None:
        mask &= sample["step"] <= step_max
    matched = sample.loc[mask]
    chosen = (
        matched if len(matched) <= limit else matched.sample(limit, random_state=seed)
    )
    points = [
        SamplePointOut(label=row.pop("isFraud"), **row)
        for row in chosen.sort_values("step").to_dict("records")
    ]
    return SampleOut(
        total_in_sample=len(sample),
        matched=len(matched),
        returned=len(points),
        meta=meta,
        points=points,
    )

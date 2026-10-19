from typing import Any

import pandas as pd

from app.visualization.usecases.use_visualization_profile import unavailable
from app.visualization.visualization_sample import filter_sample
from app.visualization.visualization_schema import SampleOut


def execute(
    sample: pd.DataFrame | None,
    metrics: Any,
    *,
    types: list[str] | None,
    step_min: int | None,
    step_max: int | None,
    score_min: float,
    score_max: float,
    limit: int,
) -> SampleOut:
    """Muestra de test con score y puntos en 3D (trae más fraudes de lo normal)"""
    if sample is None:
        raise unavailable("La muestra de visualización")
    meta = (getattr(metrics, "sample", None) or {}) if metrics is not None else {}
    return filter_sample(
        sample,
        meta,
        types=types,
        step_min=step_min,
        step_max=step_max,
        score_min=score_min,
        score_max=score_max,
        limit=limit,
    )

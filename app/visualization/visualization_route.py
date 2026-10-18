from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.prediction.prediction_schema import TransactionType
from app.visualization.visualization_sample import filter_sample
from app.visualization.visualization_schema import DatasetProfileOut, SampleOut
from utils.auth import get_current_user

router = APIRouter(tags=["visualization"], dependencies=[Depends(get_current_user)])

MAX_POINTS = 5000


def unavailable(what: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"{what} no está disponible: copia los artefactos del entrenamiento",
    )


@router.get("/dataset/profile", response_model=DatasetProfileOut)
def profile_route(request: Request) -> Any:
    if request.app.state.profile is None:
        raise unavailable("El perfil del dataset")
    return request.app.state.profile


@router.get("/visualization/sample", response_model=SampleOut)
def sample_route(
    request: Request,
    types: Annotated[list[TransactionType] | None, Query()] = None,
    step_min: Annotated[int | None, Query(ge=0)] = None,
    step_max: Annotated[int | None, Query(ge=0)] = None,
    score_min: Annotated[float, Query(ge=0, le=1)] = 0.0,
    score_max: Annotated[float, Query(ge=0, le=1)] = 1.0,
    limit: Annotated[int, Query(ge=1, le=MAX_POINTS)] = 2000,
) -> SampleOut:
    """Muestra filtrada del conjunto de test con score del modelo y PCA 3D. Con fraudes
    sobrerrepresentados: la proporción real está en `meta.population_fraud_rate`."""
    sample = request.app.state.sample
    if sample is None:
        raise unavailable("La muestra de visualización")
    metrics = request.app.state.metrics
    meta = (getattr(metrics, "sample", None) or {}) if metrics is not None else {}
    return filter_sample(
        sample,
        meta,
        types=list(types) if types else None,
        step_min=step_min,
        step_max=step_max,
        score_min=score_min,
        score_max=score_max,
        limit=limit,
    )

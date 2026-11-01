# fastapi
from fastapi import APIRouter, Depends, Query, Request
from typing import Annotated

# dependencias
from app.auth.auth_dependency import require_permission

# casos de uso
from app.visualization.usecases.use_visualization_profile import execute as profile_visualization_execute
from app.visualization.usecases.use_visualization_sample import execute as sample_visualization_execute

# esquemas
from app.prediction.prediction_schema import TransactionType
from app.visualization.visualization_schema import DatasetProfileOut, SampleOut

router = APIRouter(
    tags=["visualization"],
    dependencies=[Depends(require_permission("visualizacion", "ver"))],
)

MAX_POINTS = 5000


@router.get("/dataset/profile", response_model=DatasetProfileOut)
def profile_visualization_endpoint(request: Request):
    """Perfil del dataset de entrenamiento"""
    return profile_visualization_execute(profile=request.app.state.profile)


@router.get("/visualization/sample", response_model=SampleOut)
def sample_visualization_endpoint(
    request: Request,
    types: Annotated[list[TransactionType] | None, Query()] = None,
    step_min: Annotated[int | None, Query(ge=0)] = None,
    step_max: Annotated[int | None, Query(ge=0)] = None,
    score_min: Annotated[float, Query(ge=0, le=1)] = 0.0,
    score_max: Annotated[float, Query(ge=0, le=1)] = 1.0,
    limit: Annotated[int, Query(ge=1, le=MAX_POINTS)] = 2000,
):
    """Muestra de test con score y puntos en 3D (trae más fraudes de lo normal)"""
    return sample_visualization_execute(
        sample=request.app.state.sample,
        metrics=request.app.state.metrics,
        types=list(types) if types else None,
        step_min=step_min,
        step_max=step_max,
        score_min=score_min,
        score_max=score_max,
        limit=limit,
    )

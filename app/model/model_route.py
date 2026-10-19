# fastapi
from fastapi import APIRouter, Depends, Request

# dependencias
from app.auth.auth_dependency import require_permission

# esquemas
from app.model.model_schema import (
    ExperimentOut,
    ExperimentsOut,
    HealthOut,
    MetricsOut,
    ModelInfoOut,
)

# casos de uso
from app.model.usecases.use_model_experiment_list import (
    execute as list_experiment_execute,
)
from app.model.usecases.use_model_experiment_view import (
    execute as view_experiment_execute,
)
from app.model.usecases.use_model_health import execute as health_model_execute
from app.model.usecases.use_model_info import execute as info_model_execute
from app.model.usecases.use_model_metrics import execute as metrics_model_execute

router = APIRouter(tags=["model"])


@router.get("/health", response_model=HealthOut)
def health_endpoint(request: Request):
    """Revisa si la API y el modelo están funcionando"""
    return health_model_execute(
        model=request.app.state.model, metrics=request.app.state.metrics
    )


@router.get(
    "/metrics",
    response_model=MetricsOut,
    response_model_exclude_none=True,
    dependencies=[Depends(require_permission("modelo", "ver"))],
)
def metrics_model_endpoint(request: Request):
    """Métricas del modelo desplegado"""
    return metrics_model_execute(metrics=request.app.state.metrics)


@router.get(
    "/model/info",
    response_model=ModelInfoOut,
    dependencies=[Depends(require_permission("modelo", "ver"))],
)
def info_model_endpoint(request: Request):
    """Versión, variables y umbrales del modelo que está cargado"""
    return info_model_execute(
        model=request.app.state.model,
        metrics=request.app.state.metrics,
        policy=request.app.state.policy,
    )


@router.get(
    "/experiments",
    response_model=ExperimentsOut,
    dependencies=[Depends(require_permission("modelo", "ver"))],
)
def list_experiment_endpoint(request: Request):
    """Lista de los modelos que se probaron, para compararlos"""
    return list_experiment_execute(
        experiments=request.app.state.experiments, metrics=request.app.state.metrics
    )


@router.get(
    "/experiments/{version}",
    response_model=ExperimentOut,
    dependencies=[Depends(require_permission("modelo", "ver"))],
)
def view_experiment_endpoint(version: str, request: Request):
    """Ver un experimento por su versión"""
    return view_experiment_execute(
        experiments=request.app.state.experiments,
        metrics=request.app.state.metrics,
        version=version,
    )

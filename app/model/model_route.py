# fastapi
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

# dependencias
from config.database import get_db
from app.auth.auth_dependency import require_permission
from app.prediction.prediction_dependency import get_base_policy, get_policy
from app.prediction.prediction_policy import RiskPolicy

# casos de uso
from app.model.usecases.use_model_health import execute as health_model_execute
from app.model.usecases.use_model_metrics import execute as metrics_model_execute
from app.model.usecases.use_model_info import execute as info_model_execute
from app.model.usecases.use_model_experiment_list import execute as list_experiment_execute
from app.model.usecases.use_model_experiment_view import execute as view_experiment_execute
from app.model.usecases.use_model_policy_view import execute as view_policy_execute
from app.model.usecases.use_model_policy_update import execute as update_policy_execute
from app.model.usecases.use_model_policy_reset import execute as reset_policy_execute

# entidades
from app.user.user_entity import User

# esquemas
from app.model.model_schema import HealthOut, MetricsOut, ModelInfoOut, ExperimentsOut, ExperimentOut, PolicyIn, PolicyOut

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
def info_model_endpoint(request: Request, policy: RiskPolicy = Depends(get_policy)):
    """Versión, variables y umbrales del modelo que está cargado"""
    return info_model_execute(
        model=request.app.state.model,
        metrics=request.app.state.metrics,
        policy=policy,
    )

@router.get(
    "/model/policy",
    response_model=PolicyOut,
    dependencies=[Depends(require_permission("modelo", "ver"))],
)
def view_policy_endpoint(
    db: Session = Depends(get_db), base: RiskPolicy = Depends(get_base_policy)
):
    """Umbrales de decisión en uso y los del entrenamiento"""
    return view_policy_execute(db=db, base=base)

@router.put("/model/policy", response_model=PolicyOut)
def update_policy_endpoint(
    payload: PolicyIn,
    db: Session = Depends(get_db),
    base: RiskPolicy = Depends(get_base_policy),
    current_user: User = Depends(require_permission("modelo", "editar")),
):
    """Cambia los umbrales; las predicciones siguientes ya los usan"""
    return update_policy_execute(db=db, current_user=current_user, base=base, payload=payload)

@router.delete("/model/policy", response_model=PolicyOut)
def reset_policy_endpoint(
    db: Session = Depends(get_db),
    base: RiskPolicy = Depends(get_base_policy),
    current_user: User = Depends(require_permission("modelo", "editar")),
):
    """Vuelve a los umbrales del entrenamiento (o de FRAUD_THRESHOLD)"""
    return reset_policy_execute(db=db, current_user=current_user, base=base)

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
    experiment = view_experiment_execute(experiments=request.app.state.experiments, metrics=request.app.state.metrics, version=version)
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El experimento no existe")
    return experiment
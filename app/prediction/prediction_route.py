# fastapi
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.orm import Session
from typing import Any

# dependencias
from config.database import get_db
from config.settings import settings
from app.auth.auth_dependency import RateLimited, get_current_user, require_permission
from app.prediction.prediction_dependency import get_model, get_policy, model_version
from app.prediction.prediction_policy import RiskPolicy

# casos de uso
from app.prediction.usecases.use_prediction_predict import execute as predict_prediction_execute
from app.prediction.usecases.use_prediction_history import execute as history_prediction_execute
from app.prediction.usecases.use_prediction_csv import execute as csv_prediction_execute

# entidades
from app.user.user_entity import User

# esquemas
from app.prediction.prediction_schema import PredictIn, PredictOut, PredictionHistoryOut

# Primero se revisa la sesión, para que sin login dé 401 antes que otro error
router = APIRouter(tags=["prediction"], dependencies=[Depends(get_current_user)])


@router.post("/predict", response_model=PredictOut, dependencies=[RateLimited])
def predict_endpoint(
    request: Request,
    payload: PredictIn,
    explain: bool = False,
    current_user: User = Depends(require_permission("predicciones", "crear")),
    model: Any = Depends(get_model),
    policy: RiskPolicy = Depends(get_policy),
    db: Session = Depends(get_db),
):
    """Analiza transacciones; con `explain=true` dice qué subió el score"""
    return predict_prediction_execute(
        db=db,
        current_user=current_user,
        model=model,
        policy=policy,
        transactions=payload.transactions,
        explain=explain,
        model_version=model_version(request),
    )


@router.get("/predictions", response_model=PredictionHistoryOut)
def history_prediction_endpoint(
    all: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=5, ge=1, le=100),
    alerts_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("predicciones", "ver")),
):
    """Últimas transacciones analizadas; con `all=true` el root ve las de todos"""
    return history_prediction_execute(
        db=db,
        current_user=current_user,
        all=all,
        page=page,
        page_size=page_size,
        alerts_only=alerts_only,
    )


@router.post("/predict/batch", response_model=PredictOut, dependencies=[RateLimited])
def csv_prediction_endpoint(
    request: Request,
    file: UploadFile,
    current_user: User = Depends(require_permission("predicciones", "crear")),
    model: Any = Depends(get_model),
    policy: RiskPolicy = Depends(get_policy),
    db: Session = Depends(get_db),
):
    """Analiza un CSV de PaySim (máximo MAX_UPLOAD_MB y MAX_BATCH_ROWS filas)"""
    if file.size is not None and file.size > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"El archivo supera el máximo de {settings.max_upload_mb} MB",
        )
    return csv_prediction_execute(
        db=db,
        current_user=current_user,
        model=model,
        policy=policy,
        original=file.file.read(),
        file_name=file.filename or "lote.csv",
        max_rows=settings.max_batch_rows,
        archive=request.app.state.batch_archive,
        model_version=model_version(request),
    )

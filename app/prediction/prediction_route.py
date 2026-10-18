from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.prediction.prediction_policy import RiskPolicy
from app.prediction.prediction_repository import PredictionRepository
from app.prediction.prediction_schema import (
    PredictIn,
    PredictionHistoryOut,
    PredictOut,
)
from app.prediction.usecases.use_prediction_csv import InvalidCSVError, predict_csv_file
from app.prediction.usecases.use_prediction_history import (
    prediction_history,
    save_predictions,
)
from app.prediction.usecases.use_prediction_predict import predict_transactions
from config.settings import settings
from utils.auth import CurrentUser, Users, get_current_user, is_admin
from utils.rate_limit import RateLimited

router = APIRouter(tags=["prediction"], dependencies=[Depends(get_current_user)])


def get_model(request: Request) -> Any:
    model = request.app.state.model
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El modelo no está disponible",
        )
    return model


Model = Annotated[Any, Depends(get_model)]


def get_policy(request: Request) -> RiskPolicy:
    return request.app.state.policy


Policy = Annotated[RiskPolicy, Depends(get_policy)]


def model_version(request: Request) -> str | None:
    metrics = request.app.state.metrics
    return getattr(metrics, "version", None) if metrics is not None else None


def get_predictions(request: Request) -> PredictionRepository:
    predictions = request.app.state.predictions
    if predictions is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El historial de predicciones no está configurado",
        )
    return predictions


Predictions = Annotated[PredictionRepository, Depends(get_predictions)]


@router.post("/predict", response_model=PredictOut, dependencies=[RateLimited])
def predict_route(
    request: Request,
    payload: PredictIn,
    model: Model,
    policy: Policy,
    username: CurrentUser,
    explain: bool = False,
) -> PredictOut:
    """Predice hasta MAX_BATCH_ROWS transacciones. Con `explain=true` (hasta 10) cada
    predicción trae los aportes por variable al score."""
    result = predict_transactions(
        model,
        payload.transactions,
        policy,
        with_explanation=explain,
        model_version=model_version(request),
    )
    save_predictions(
        request.app.state.predictions, username, payload.transactions, result
    )
    return result


@router.get("/predictions", response_model=PredictionHistoryOut)
def history_route(
    username: CurrentUser,
    users: Users,
    predictions: Predictions,
    all: bool = False,
    limit: int = Query(default=5, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    alerts_only: bool = False,
) -> PredictionHistoryOut:
    """Últimas transacciones analizadas una a una; `all=true` (solo admin) de todos."""
    if all and not is_admin(users, username):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un administrador puede ver las predicciones de todos",
        )
    return prediction_history(
        predictions, None if all else username, limit, offset, alerts_only
    )


@router.post("/predict/batch", response_model=PredictOut, dependencies=[RateLimited])
@router.post(
    "/predict/csv",
    response_model=PredictOut,
    dependencies=[RateLimited],
    deprecated=True,
)
def predict_csv_route(
    request: Request,
    file: UploadFile,
    model: Model,
    policy: Policy,
    username: CurrentUser,
) -> PredictOut:
    """Predice un CSV de PaySim (máximo MAX_UPLOAD_MB y MAX_BATCH_ROWS filas)."""
    if file.size is not None and file.size > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"El archivo supera el máximo de {settings.max_upload_mb} MB",
        )
    try:
        return predict_csv_file(
            model,
            policy,
            file.file.read(),
            file_name=file.filename or "lote.csv",
            username=username,
            storage=request.app.state.storage,
            batches=request.app.state.batches,
            model_version=model_version(request),
        )
    except InvalidCSVError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    except ValidationError as error:
        raise RequestValidationError(
            error.errors(include_url=False, include_context=False)
        ) from error

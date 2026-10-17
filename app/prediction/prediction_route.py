from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.prediction.prediction_schema import PredictIn, PredictOut
from app.prediction.usecases.use_prediction_csv import InvalidCSVError, predict_csv_file
from app.prediction.usecases.use_prediction_predict import predict_transactions
from config.settings import settings
from utils.auth import CurrentUser, get_current_user

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


@router.post("/predict", response_model=PredictOut)
def predict_route(payload: PredictIn, model: Model) -> PredictOut:
    return predict_transactions(model, payload.transactions)


@router.post("/predict/csv", response_model=PredictOut)
def predict_csv_route(
    request: Request, file: UploadFile, model: Model, username: CurrentUser
) -> PredictOut:
    if file.size is not None and file.size > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"El archivo supera el máximo de {settings.max_upload_mb} MB",
        )
    try:
        return predict_csv_file(
            model,
            file.file.read(),
            file_name=file.filename or "lote.csv",
            username=username,
            storage=request.app.state.storage,
            batches=request.app.state.batches,
        )
    except InvalidCSVError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    except ValidationError as error:
        raise RequestValidationError(
            error.errors(include_url=False, include_context=False)
        ) from error

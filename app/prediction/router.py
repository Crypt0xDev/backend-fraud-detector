from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.prediction import service
from app.prediction.schemas import PredictIn, PredictOut, Transaction
from app.shared.config import settings

router = APIRouter(tags=["prediction"])


def get_model(request: Request) -> Any:
    model = request.app.state.model
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El modelo no está disponible",
        )
    return model


def respond(model: Any, transactions: list[Transaction]) -> PredictOut:
    threshold = settings.fraud_threshold
    return PredictOut(
        threshold=threshold,
        predictions=service.predict(model, transactions, threshold),
    )


@router.post("/predict", response_model=PredictOut)
def predict(
    payload: PredictIn, model: Annotated[Any, Depends(get_model)]
) -> PredictOut:
    return respond(model, payload.transactions)


@router.post("/predict/csv", response_model=PredictOut)
def predict_csv(
    file: UploadFile, model: Annotated[Any, Depends(get_model)]
) -> PredictOut:
    try:
        transactions = service.read_csv(file.file, settings.max_batch_rows)
    except service.InvalidCSVError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    except ValidationError as error:
        raise RequestValidationError(
            error.errors(include_url=False, include_context=False)
        ) from error
    return respond(model, transactions)

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.batch.batch_repository import BatchRepository
from utils.storage import FileStorage


def unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="El historial de lotes no está configurado",
    )


def get_batches(request: Request) -> BatchRepository:
    if request.app.state.batches is None:
        raise unavailable()
    return request.app.state.batches


def get_storage(request: Request) -> FileStorage:
    if request.app.state.storage is None:
        raise unavailable()
    return request.app.state.storage


Batches = Annotated[BatchRepository, Depends(get_batches)]
Storage = Annotated[FileStorage, Depends(get_storage)]

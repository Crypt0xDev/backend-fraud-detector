from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from app.batch.batch_dependency import Batches, Storage
from app.batch.batch_schema import BatchFile, BatchFileUrlOut, BatchOut
from app.batch.usecases.use_batch_delete import delete_batch
from app.batch.usecases.use_batch_file_url import batch_file_url
from app.batch.usecases.use_batch_list import list_batches
from app.batch.usecases.use_batch_view import BatchNotFoundError
from utils.auth import CurrentUser
from utils.storage import StorageError

router = APIRouter(prefix="/batches", tags=["batches"])


def not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="El lote no existe"
    )


def storage_failed() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="No se pudo acceder al almacenamiento de archivos",
    )


@router.get("", response_model=list[BatchOut])
def list_route(username: CurrentUser, batches: Batches) -> list[BatchOut]:
    return list_batches(batches, username)


@router.get("/{batch_id}/files/{kind}", response_model=BatchFileUrlOut)
def file_url_route(
    batch_id: UUID,
    kind: BatchFile,
    username: CurrentUser,
    batches: Batches,
    storage: Storage,
) -> BatchFileUrlOut:
    try:
        return batch_file_url(batches, storage, username, batch_id, kind)
    except BatchNotFoundError as error:
        raise not_found() from error
    except StorageError as error:
        raise storage_failed() from error


@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route(
    batch_id: UUID, username: CurrentUser, batches: Batches, storage: Storage
) -> Response:
    try:
        delete_batch(batches, storage, username, batch_id)
    except BatchNotFoundError as error:
        raise not_found() from error
    except StorageError as error:
        raise storage_failed() from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)

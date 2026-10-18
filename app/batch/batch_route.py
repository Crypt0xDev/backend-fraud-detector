from uuid import UUID
from zoneinfo import available_timezones

from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.responses import FileResponse

from app.batch.batch_dependency import Batches, Storage
from app.batch.batch_schema import (
    BatchFile,
    BatchFileUrlOut,
    BatchPageOut,
    BatchStatsOut,
)
from app.batch.usecases.use_batch_delete import delete_batch
from app.batch.usecases.use_batch_file_url import batch_file_url
from app.batch.usecases.use_batch_list import list_batches
from app.batch.usecases.use_batch_stats import batch_stats
from app.batch.usecases.use_batch_view import BatchNotFoundError
from utils.auth import CurrentUser, Users, is_admin
from utils.storage import LocalStorage, StorageError
from utils.token import decode_download_token

router = APIRouter(prefix="/batches", tags=["batches"])

DOWNLOAD_PATH = "/download"


def not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="El lote no existe"
    )


def storage_failed() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="No se pudo acceder al almacenamiento de archivos",
    )


def scope(users: Users, username: str) -> str | None:
    """None (todos los lotes) para un admin; el propio usuario para el resto."""
    return None if is_admin(users, username) else username


def owner(users: Users, username: str, all: bool) -> str | None:
    if all and not is_admin(users, username):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un administrador puede ver los lotes de todos",
        )
    return None if all else username


@router.get("", response_model=BatchPageOut)
def list_route(
    username: CurrentUser,
    users: Users,
    batches: Batches,
    all: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
) -> BatchPageOut:
    """Lotes propios, paginados; con `all=true` (solo admin), los de todos."""
    return list_batches(batches, owner(users, username, all), page, page_size)


@router.get("/stats", response_model=BatchStatsOut)
def stats_route(
    username: CurrentUser,
    users: Users,
    batches: Batches,
    all: bool = False,
    days: int = Query(default=14, ge=1, le=90),
    tz: str = "UTC",
) -> BatchStatsOut:
    """Totales y serie diaria de los lotes; `all=true` (solo admin) suma los de todos.
    `tz` (IANA, p. ej. America/Lima) define a qué día pertenece cada lote."""
    if tz not in available_timezones():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Zona horaria no válida: {tz}",
        )
    return batch_stats(batches, owner(users, username, all), days, tz)


@router.get("/{batch_id}/files/{kind}", response_model=BatchFileUrlOut)
def file_url_route(
    batch_id: UUID,
    kind: BatchFile,
    username: CurrentUser,
    users: Users,
    batches: Batches,
    storage: Storage,
) -> BatchFileUrlOut:
    try:
        return batch_file_url(batches, storage, scope(users, username), batch_id, kind)
    except BatchNotFoundError as error:
        raise not_found() from error
    except StorageError as error:
        raise storage_failed() from error


@router.get(DOWNLOAD_PATH, response_class=FileResponse)
def download_route(token: str, storage: Storage) -> FileResponse:
    """Descarga de un archivo del almacenamiento local. La autoriza el token de la URL
    firmada (5 min), no la sesión, para que funcione como enlace directo."""
    if not isinstance(storage, LocalStorage):
        raise not_found()
    claims = decode_download_token(token)
    if claims is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El enlace de descarga no es válido o expiró",
        )
    path, name = claims
    try:
        target = storage.resolve(path)
    except StorageError as error:
        raise not_found() from error
    if not target.is_file():
        raise not_found()
    return FileResponse(target, media_type="text/csv", filename=name)


@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route(
    batch_id: UUID,
    username: CurrentUser,
    users: Users,
    batches: Batches,
    storage: Storage,
) -> Response:
    try:
        delete_batch(batches, storage, scope(users, username), batch_id)
    except BatchNotFoundError as error:
        raise not_found() from error
    except StorageError as error:
        raise storage_failed() from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)

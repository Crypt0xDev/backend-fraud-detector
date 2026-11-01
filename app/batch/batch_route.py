# fastapi
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import UUID

# dependencias
from config.database import get_db
from app.auth.auth_dependency import require_permission
from app.batch.batch_dependency import get_storage
from utils.storage import FileStorage, LocalStorage, StorageError
from utils.token import decode_download_token

# casos de uso
from app.batch.usecases.use_batch_list import execute as list_batch_execute
from app.batch.usecases.use_batch_stats import execute as stats_batch_execute
from app.batch.usecases.use_batch_file_url import execute as file_url_batch_execute
from app.batch.usecases.use_batch_delete import execute as delete_batch_execute

# entidades
from app.user.user_entity import User

# esquemas
from app.batch.batch_schema import BatchFile, BatchPageOut, BatchStatsOut, BatchFileUrlOut

router = APIRouter(prefix="/batches", tags=["batches"])

DOWNLOAD_PATH = "/download"


def not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="El lote no existe"
    )


@router.get("", response_model=BatchPageOut)
def list_batch_endpoint(
    all: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lotes", "ver")),
):
    """Listar los lotes del usuario; con `all` el root ve todos"""
    return list_batch_execute(
        db=db, current_user=current_user, all=all, page=page, page_size=page_size
    )


@router.get("/stats", response_model=BatchStatsOut)
def stats_batch_endpoint(
    all: bool = False,
    days: int = Query(default=14, ge=1, le=90),
    tz: str = "UTC",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lotes", "ver")),
):
    """Totales de los lotes y cuántos hubo por día"""
    return stats_batch_execute(
        db=db, current_user=current_user, all=all, days=days, tz=tz
    )


@router.get("/{batch_id}/files/{kind}", response_model=BatchFileUrlOut)
def file_url_batch_endpoint(
    batch_id: UUID,
    kind: BatchFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lotes", "ver")),
    storage: FileStorage = Depends(get_storage),
):
    """Enlace de 5 minutos para descargar el CSV original o el de resultados"""
    url = file_url_batch_execute(db=db, current_user=current_user, storage=storage, batch_id=batch_id, kind=kind)
    if url is None:
        raise not_found()
    return url


@router.get(DOWNLOAD_PATH, response_class=FileResponse)
def download_route(token: str, storage: FileStorage = Depends(get_storage)):
    """Descarga de un archivo del almacenamiento local"""
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


@router.delete(
    "/{batch_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        204: {"description": "Lote eliminado correctamente"},
        404: {"description": "Lote no encontrado"},
    },
)
def delete_batch_endpoint(
    batch_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lotes", "eliminar")),
    storage: FileStorage = Depends(get_storage),
):
    """Eliminar un lote y sus archivos"""
    if not delete_batch_execute(db=db, current_user=current_user, storage=storage, batch_id=batch_id):
        raise not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

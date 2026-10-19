from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.batch.batch_schema import BatchFile, BatchFileUrlOut
from app.batch.batch_storage import download_name, object_path
from app.batch.usecases.use_batch_view import execute as view_batch_execute
from app.user.user_entity import User
from utils.storage import FileStorage, StorageError

SIGNED_URL_SECONDS = 300


def execute(
    db: Session,
    current_user: User,
    storage: FileStorage,
    batch_id: UUID,
    kind: BatchFile,
) -> BatchFileUrlOut | None:
    batch = view_batch_execute(db=db, current_user=current_user, batch_id=batch_id)
    if batch is None:
        return None

    try:
        url = storage.signed_url(
            object_path(batch_id, kind), SIGNED_URL_SECONDS, download_name(batch, kind)
        )
    except StorageError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo acceder al almacenamiento de archivos",
        ) from error
    return BatchFileUrlOut(url=url, expires_in=SIGNED_URL_SECONDS)

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.batch.batch_storage import object_paths
from app.batch.usecases.use_batch_view import execute as view_batch_execute
from app.user.user_entity import User
from utils.storage import FileStorage, StorageError


def execute(
    db: Session, current_user: User, storage: FileStorage, batch_id: UUID
) -> bool:
    batch = view_batch_execute(db=db, current_user=current_user, batch_id=batch_id)
    if batch is None:
        return False

    try:
        storage.delete(object_paths(batch_id))
    except StorageError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo acceder al almacenamiento de archivos",
        ) from error

    db.delete(batch)
    db.commit()
    return True

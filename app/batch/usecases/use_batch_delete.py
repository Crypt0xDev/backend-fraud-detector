from uuid import UUID

from sqlalchemy.orm import Session

from app.batch.batch_storage import object_paths
from app.batch.usecases.use_batch_view import execute as view_batch_execute
from app.user.user_entity import User
from utils.errors import StorageFailureError
from utils.storage import FileStorage, StorageError


def execute(
    db: Session, current_user: User, storage: FileStorage, batch_id: UUID
) -> None:
    batch = view_batch_execute(db=db, current_user=current_user, batch_id=batch_id)

    try:
        storage.delete(object_paths(batch_id))
    except StorageError as error:
        raise StorageFailureError(
            "No se pudo acceder al almacenamiento de archivos"
        ) from error

    db.delete(batch)
    db.commit()

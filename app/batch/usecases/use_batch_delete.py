from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.batch.batch_storage import object_paths
from app.batch.usecases.use_batch_view import execute as view_batch_execute
from app.user.user_entity import User
from utils.storage import FileStorage, StorageError


def execute(db: Session, current_user: User, storage: FileStorage, batch_id: UUID) -> bool:
    # Verificar que el lote exista y el usuario lo pueda ver
    batch = view_batch_execute(db=db, current_user=current_user, batch_id=batch_id)

    if batch is None:
        return False

    # Primero se borra el lote sin confirmar: si fallan los archivos se deshace,
    # y si falla la base no se pierden archivos de un lote que sigue existiendo
    db.delete(batch)
    db.flush()
    try:
        storage.delete(object_paths(batch_id))
    except StorageError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo acceder al almacenamiento de archivos"
        ) from error

    db.commit()
    return True

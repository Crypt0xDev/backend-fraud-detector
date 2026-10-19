from uuid import UUID

from sqlalchemy.orm import Session

from app.batch.batch_entity import Batch
from app.batch.batch_storage import object_paths
from app.batch.usecases.use_batch_save import execute as save_batch_execute
from utils.storage import FileStorage


class StorageBatchArchive:
    """Guarda los CSV analizados en el almacenamiento"""

    def __init__(self, storage: FileStorage):
        self.storage = storage

    def save(
        self,
        db: Session,
        *,
        username: str,
        file_name: str,
        original: bytes,
        predictions: bytes,
        flagged_rows: int,
        total_rows: int,
        threshold: float,
    ) -> UUID | None:
        return save_batch_execute(
            db,
            self.storage,
            username=username,
            file_name=file_name,
            original=original,
            predictions=predictions,
            flagged_rows=flagged_rows,
            total_rows=total_rows,
            threshold=threshold,
        )


class BatchFilesCleaner:
    """Borra los archivos de un usuario cuando se elimina su cuenta"""

    def __init__(self, storage: FileStorage):
        self.storage = storage

    def delete_user_data(self, db: Session, username: str) -> None:
        ids = db.query(Batch.id).filter(Batch.username == username).all()
        paths = [path for (batch_id,) in ids for path in object_paths(batch_id)]
        if paths:
            self.storage.delete(paths)

import logging
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.batch.batch_entity import Batch
from app.batch.batch_storage import object_paths
from utils.storage import FileStorage, StorageError

logger = logging.getLogger(__name__)


def execute(
    db: Session,
    storage: FileStorage,
    *,
    username: str,
    file_name: str,
    original: bytes,
    predictions: bytes,
    flagged_rows: int,
    total_rows: int,
    threshold: float,
    model_version: str | None = None,
) -> UUID | None:
    """Guarda los dos CSV y el lote. Si falla, igual se devuelve el análisis"""
    batch_id = uuid4()
    input_path, predictions_path = paths = object_paths(batch_id)
    try:
        storage.upload(input_path, original, "text/csv")
        storage.upload(predictions_path, predictions, "text/csv")
        db.add(
            Batch(
                id=batch_id,
                username=username,
                file_name=file_name,
                total_rows=total_rows,
                flagged_rows=flagged_rows,
                threshold=threshold,
                model_version=model_version,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("No se pudo guardar el lote %s", batch_id)
        try:
            storage.delete(paths)
        except StorageError:
            logger.exception("No se pudieron borrar los archivos del lote %s", batch_id)
        return None
    return batch_id

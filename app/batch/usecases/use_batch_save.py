import logging
from uuid import UUID, uuid4

from app.batch.batch_repository import BatchRepository
from app.batch.batch_storage import object_paths
from utils.storage import StorageError, SupabaseStorage

logger = logging.getLogger(__name__)


def save_batch(
    storage: SupabaseStorage,
    batches: BatchRepository,
    *,
    username: str,
    file_name: str,
    original: bytes,
    predictions: bytes,
    flagged_rows: int,
    total_rows: int,
    threshold: float,
) -> UUID | None:
    """Guarda ambos CSV y el registro; si algo falla, el análisis se devuelve igual."""
    batch_id = uuid4()
    input_path, predictions_path = paths = object_paths(batch_id)
    try:
        storage.upload(input_path, original, "text/csv")
        storage.upload(predictions_path, predictions, "text/csv")
        batches.add(batch_id, username, file_name, total_rows, flagged_rows, threshold)
    except Exception:
        logger.exception("No se pudo guardar el lote %s", batch_id)
        try:
            storage.delete(paths)
        except StorageError:
            logger.exception("No se pudieron borrar los archivos del lote %s", batch_id)
        return None
    return batch_id

from uuid import UUID

from app.batch.batch_repository import BatchRepository
from app.batch.batch_storage import object_paths
from app.batch.usecases.use_batch_view import view_batch
from utils.storage import FileStorage


def delete_batch(
    batches: BatchRepository, storage: FileStorage, owner: str | None, batch_id: UUID
) -> None:
    view_batch(batches, owner, batch_id)
    storage.delete(object_paths(batch_id))
    batches.delete(owner, batch_id)

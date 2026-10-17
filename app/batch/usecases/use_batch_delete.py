from uuid import UUID

from app.batch.batch_repository import BatchRepository
from app.batch.batch_storage import object_paths
from app.batch.usecases.use_batch_view import view_batch
from utils.storage import SupabaseStorage


def delete_batch(
    batches: BatchRepository, storage: SupabaseStorage, username: str, batch_id: UUID
) -> None:
    view_batch(batches, username, batch_id)
    storage.delete(object_paths(batch_id))
    batches.delete(username, batch_id)

from uuid import UUID

from app.batch.batch_repository import BatchRepository
from app.batch.batch_schema import BatchOut


class BatchNotFoundError(Exception):
    pass


def view_batch(batches: BatchRepository, owner: str | None, batch_id: UUID) -> BatchOut:
    batch = batches.get(owner, batch_id)
    if batch is None:
        raise BatchNotFoundError
    return batch

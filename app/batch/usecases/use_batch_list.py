from app.batch.batch_repository import BatchRepository
from app.batch.batch_schema import BatchOut


def list_batches(batches: BatchRepository, username: str) -> list[BatchOut]:
    return batches.list(username)

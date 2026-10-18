from app.batch.batch_repository import BatchRepository
from app.batch.batch_schema import BatchPageOut


def list_batches(
    batches: BatchRepository, owner: str | None, page: int, page_size: int
) -> BatchPageOut:
    return BatchPageOut(
        items=batches.list(owner, limit=page_size, offset=(page - 1) * page_size),
        total=batches.count(owner),
        page=page,
        page_size=page_size,
    )

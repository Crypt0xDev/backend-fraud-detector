from uuid import UUID

from app.batch.batch_repository import BatchRepository
from app.batch.batch_schema import BatchFile, BatchFileUrlOut
from app.batch.batch_storage import download_name, object_path
from app.batch.usecases.use_batch_view import view_batch
from utils.storage import FileStorage

SIGNED_URL_SECONDS = 300


def batch_file_url(
    batches: BatchRepository,
    storage: FileStorage,
    owner: str | None,
    batch_id: UUID,
    kind: BatchFile,
) -> BatchFileUrlOut:
    batch = view_batch(batches, owner, batch_id)
    url = storage.signed_url(
        object_path(batch_id, kind), SIGNED_URL_SECONDS, download_name(batch, kind)
    )
    return BatchFileUrlOut(url=url, expires_in=SIGNED_URL_SECONDS)

from pathlib import PurePath
from uuid import UUID

from app.batch.batch_schema import BatchFile

BATCH_FILES: tuple[BatchFile, ...] = ("input", "predictions")


def object_path(batch_id: UUID, kind: BatchFile) -> str:
    return f"{batch_id}/{kind}.csv"


def object_paths(batch_id: UUID) -> list[str]:
    return [object_path(batch_id, kind) for kind in BATCH_FILES]


def download_name(file_name: str, kind: BatchFile) -> str:
    stem = PurePath(file_name).stem or "lote"
    return f"{stem}_predicciones.csv" if kind == "predictions" else f"{stem}.csv"

from typing import Protocol
from uuid import UUID

from sqlalchemy.orm import Session


class BatchArchive(Protocol):
    """Guarda un CSV analizado en el historial (lo hace batch)"""

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
        model_version: str | None = None,
    ) -> UUID | None: ...

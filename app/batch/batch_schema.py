# python
from datetime import date, datetime
from typing import Literal
from uuid import UUID

# pydantic
from pydantic import BaseModel

BatchFile = Literal["input", "predictions"]


# Inicio del response de un lote
class BatchOut(BaseModel):
    id: UUID
    username: str | None = None
    file_name: str
    total_rows: int
    flagged_rows: int
    threshold: float
    model_version: str | None = None
    created_at: datetime


class BatchPageOut(BaseModel):
    items: list[BatchOut]
    total: int
    page: int
    page_size: int
# Fin del response de un lote


# Inicio del response de la descarga
class BatchFileUrlOut(BaseModel):
    url: str
    expires_in: int
# Fin del response de la descarga


# Inicio del response de las estadísticas
class BatchDayOut(BaseModel):
    day: date
    batches: int
    total_rows: int
    flagged_rows: int


class BatchStatsOut(BaseModel):
    batches: int
    total_rows: int
    flagged_rows: int
    days: list[BatchDayOut]
# Fin del response de las estadísticas

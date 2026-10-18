from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

BatchFile = Literal["input", "predictions"]


class BatchOut(BaseModel):
    id: UUID
    username: str | None = None
    file_name: str
    total_rows: int
    flagged_rows: int
    threshold: float
    created_at: datetime


class BatchPageOut(BaseModel):
    items: list[BatchOut]
    total: int
    page: int
    page_size: int


class BatchFileUrlOut(BaseModel):
    url: str
    expires_in: int


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

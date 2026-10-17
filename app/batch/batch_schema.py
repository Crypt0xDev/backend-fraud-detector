from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

BatchFile = Literal["input", "predictions"]


class BatchOut(BaseModel):
    id: UUID
    file_name: str
    total_rows: int
    flagged_rows: int
    threshold: float
    created_at: datetime


class BatchFileUrlOut(BaseModel):
    url: str
    expires_in: int

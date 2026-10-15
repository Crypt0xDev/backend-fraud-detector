from typing import Literal

from pydantic import BaseModel


class HealthOut(BaseModel):
    status: Literal["ok"]
    model_loaded: bool
    metrics_loaded: bool

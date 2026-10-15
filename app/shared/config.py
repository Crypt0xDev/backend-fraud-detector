from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    cors_origins: str = "http://localhost:3000"
    model_path: Path = BASE_DIR / "ml" / "artifacts" / "pipeline.joblib"
    metrics_path: Path = BASE_DIR / "ml" / "artifacts" / "metrics.json"
    model_sha256: str | None = None
    max_batch_rows: int = 10_000
    fraud_threshold: float = Field(default=0.5, ge=0, le=1)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @field_validator("model_path", "metrics_path")
    @classmethod
    def resolve_path(cls, value: Path) -> Path:
        return value if value.is_absolute() else BASE_DIR / value

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


settings = Settings()

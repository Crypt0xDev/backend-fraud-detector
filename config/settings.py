from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    cors_origins: str = "http://localhost:3000"
    model_path: Path = BASE_DIR / "ml" / "artifacts" / "pipeline.joblib"
    metrics_path: Path = BASE_DIR / "ml" / "artifacts" / "metrics.json"
    database_url: str | None = None
    supabase_url: str | None = None
    supabase_secret_key: str | None = None
    supabase_bucket: str = "batches"
    jwt_secret: str | None = Field(default=None, min_length=32)
    jwt_expire_minutes: int = Field(default=480, gt=0)
    admin_username: str | None = None
    admin_password: str | None = None
    model_sha256: str | None = None
    max_batch_rows: int = 10_000
    max_upload_mb: int = Field(default=20, gt=0)
    fraud_threshold: float = Field(default=0.5, ge=0, le=1)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @field_validator("model_path", "metrics_path")
    @classmethod
    def resolve_path(cls, value: Path) -> Path:
        return value if value.is_absolute() else BASE_DIR / value

    @field_validator(
        "database_url",
        "supabase_url",
        "supabase_secret_key",
        "jwt_secret",
        "admin_username",
        "admin_password",
        mode="before",
    )
    @classmethod
    def empty_to_none(cls, value: str | None) -> str | None:
        return value or None

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


settings = Settings()

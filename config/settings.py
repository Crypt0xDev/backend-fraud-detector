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
    sample_path: Path = BASE_DIR / "ml" / "artifacts" / "sample.csv"
    experiments_path: Path = BASE_DIR / "ml" / "artifacts" / "experiments.json"
    profile_path: Path = BASE_DIR / "ml" / "artifacts" / "dataset_profile.json"
    database_url: str | None = None
    storage_backend: Literal["local", "supabase"] | None = None
    storage_dir: Path = BASE_DIR / "storage"
    api_public_url: str = "http://localhost:8000"
    supabase_url: str | None = None
    supabase_secret_key: str | None = None
    supabase_bucket: str = "batches"
    jwt_secret: str | None = Field(default=None, min_length=32)
    jwt_expire_minutes: int = Field(default=480, gt=0)
    admin_username: str | None = None
    admin_password: str | None = None
    user_username: str | None = None
    user_password: str | None = None
    model_sha256: str | None = None
    max_batch_rows: int = 10_000
    max_upload_mb: int = Field(default=20, gt=0)
    # Sin valor, el umbral y los niveles de riesgo salen de metrics.json
    fraud_threshold: float | None = Field(default=None, ge=0, le=1)
    rate_limit_per_minute: int = Field(default=120, ge=0)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @field_validator(
        "model_path",
        "metrics_path",
        "sample_path",
        "experiments_path",
        "profile_path",
        "storage_dir",
    )
    @classmethod
    def resolve_path(cls, value: Path) -> Path:
        return value if value.is_absolute() else BASE_DIR / value

    @field_validator("storage_backend", mode="before")
    @classmethod
    def normalize_backend(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            return value.strip().lower() or None
        return value

    @field_validator(
        "database_url",
        "supabase_url",
        "supabase_secret_key",
        "jwt_secret",
        "admin_username",
        "admin_password",
        "user_username",
        "user_password",
        mode="before",
    )
    @classmethod
    def empty_to_none(cls, value: str | None) -> str | None:
        return value or None

    @field_validator("fraud_threshold", mode="before")
    @classmethod
    def blank_threshold(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


settings = Settings()

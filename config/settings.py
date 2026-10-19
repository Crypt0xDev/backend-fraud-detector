from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]

# Versión pública de la API
API_PREFIX = "/api/v1"


class Settings(BaseSettings):
    # Una variable vacía en el .env cuenta como no definida
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_ignore_empty=True, extra="ignore"
    )

    # API
    api_public_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:3000"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Procesos de uvicorn
    web_concurrency: int = Field(default=1, ge=1)
    rate_limit_per_minute: int = Field(default=120, ge=0)

    # Intentos de login por minuto desde una misma IP
    login_rate_limit_per_ip: int = Field(default=60, ge=0)

    # Modelo
    artifacts_dir: Path = BASE_DIR / "ml" / "artifacts"
    model_sha256: str | None = None
    model_threads: int = Field(default=1, ge=1)
    fraud_threshold: float | None = Field(default=None, ge=0, le=1)

    # Lotes
    max_batch_rows: int = 10_000
    max_upload_mb: int = Field(default=20, gt=0)

    # Base de datos
    database_url: str | None = None
    db_pool_size: int = Field(default=5, ge=1)

    # Almacenamiento de CSV
    storage_backend: Literal["local", "supabase"] | None = None
    storage_dir: Path = BASE_DIR / "storage"
    supabase_url: str | None = None
    supabase_secret_key: str | None = None
    supabase_bucket: str = "batches"

    # Auth
    jwt_secret: str | None = Field(default=None, min_length=32)
    jwt_expire_minutes: int = Field(default=480, gt=0)

    # Usuarios iniciales
    admin_username: str | None = None
    admin_password: str | None = None
    user_username: str | None = None
    user_password: str | None = None

    # Rutas relativas desde la carpeta del proyecto
    @field_validator("artifacts_dir", "storage_dir")
    @classmethod
    def resolve_path(cls, value: Path) -> Path:
        return value if value.is_absolute() else BASE_DIR / value

    # Sin JWT_SECRET cada worker inventa su clave y el login falla al azar
    @model_validator(mode="after")
    def require_jwt_secret(self) -> "Settings":
        if self.web_concurrency > 1 and not self.jwt_secret:
            raise ValueError("Define JWT_SECRET si WEB_CONCURRENCY es mayor que 1")
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


settings = Settings()

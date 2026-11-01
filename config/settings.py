from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]

# Versión pública de la API
API_PREFIX = "/api/v1"

# Bases de datos de desarrollo: con ellas JWT_SECRET puede faltar
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


class Settings(BaseSettings):
    # Una variable vacía en el .env cuenta como no definida
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_ignore_empty=True, extra="ignore"
    )

    # API
    api_public_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:3000"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    # /docs y /openapi.json; en producción conviene false
    docs_enabled: bool = True

    # Procesos de uvicorn
    web_concurrency: int = Field(default=1, ge=1)
    rate_limit_per_minute: int = Field(default=120, ge=0)

    # Intentos de login por minuto desde una misma IP
    login_rate_limit_per_ip: int = Field(default=60, ge=0)
    # IPs del frontend: solo a ellas se les cree X-Forwarded-For
    trusted_proxies: str = "127.0.0.1,::1"

    # Modelo
    artifacts_dir: Path = BASE_DIR / "ml" / "artifacts"
    model_sha256: str | None = None
    model_threads: int = Field(default=1, ge=1)
    fraud_threshold: float | None = Field(default=None, ge=0, le=1)

    # Lotes
    max_batch_rows: int = Field(default=10_000, ge=1)
    # Transacciones por petición en POST /predict; cada una queda en el historial
    max_predict_rows: int = Field(default=100, ge=1)
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

    # Admin inicial
    admin_username: str | None = None
    admin_password: str | None = None

    # Rutas relativas desde la carpeta del proyecto
    @field_validator("artifacts_dir", "storage_dir")
    @classmethod
    def resolve_path(cls, value: Path) -> Path:
        return value if value.is_absolute() else BASE_DIR / value

    # Sin JWT_SECRET cada proceso inventa uno y las sesiones se pierden al reiniciar
    @model_validator(mode="after")
    def require_jwt_secret(self) -> "Settings":
        if self.jwt_secret:
            return self
        if self.web_concurrency > 1:
            raise ValueError("Define JWT_SECRET si WEB_CONCURRENCY es mayor que 1")
        host = urlsplit(self.database_url).hostname if self.database_url else None
        if host and host not in LOCAL_HOSTS:
            raise ValueError("Define JWT_SECRET si DATABASE_URL apunta a un servidor remoto (por ejemplo Supabase)")
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]

    @property
    def trusted_proxies_set(self) -> set[str]:
        return {ip.strip() for ip in self.trusted_proxies.split(",") if ip.strip()}


settings = Settings()

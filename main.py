import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.datastructures import State

from app.batch.batch_adapter import StorageBatchArchive
from app.model.model_schema import MetricsOut
from app.prediction.prediction_features import AVAILABLE_COLUMNS
from app.prediction.prediction_policy import build_policy
from app.visualization.visualization_sample import load_sample
from config import database, entities  # registra las tablas
from config.create_default_records import run_all_seeders
from config.error_handlers import register_error_handlers
from config.routes import api_router
from config.settings import API_PREFIX, settings
from config.startup_summary import log_startup_summary
from utils.body_limit import BodySizeLimit
from utils.model_loader import load_json, load_metrics, load_model
from utils.storage import open_storage

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    with database.startup_lock():
        if database.open_database():
            with database.SessionLocal() as db:
                run_all_seeders(db)

    # Abrir el almacenamiento de los CSV (disco o Supabase)
    app.state.storage = open_storage(
        settings.storage_backend,
        local_dir=settings.storage_dir,
        download_url=settings.api_public_url.rstrip("/")
        + app.url_path_for("download_route"),
        supabase_url=settings.supabase_url,
        supabase_secret_key=settings.supabase_secret_key,
        bucket=settings.supabase_bucket,
    )
    connect_modules(app.state)

    # Cargar el modelo y los archivos del entrenamiento
    app.state.model = load_model(
        settings.artifacts_dir / "pipeline.joblib",
        settings.model_sha256,
        available_columns=AVAILABLE_COLUMNS,
        threads=settings.model_threads,
    )
    app.state.metrics = load_metrics(
        settings.artifacts_dir / "metrics.json", MetricsOut
    )
    app.state.policy = build_policy(app.state.metrics, settings.fraud_threshold)
    app.state.experiments = load_json(settings.artifacts_dir / "experiments.json")
    app.state.profile = load_json(settings.artifacts_dir / "dataset_profile.json")
    app.state.sample = load_sample(settings.artifacts_dir / "sample.csv")
    log_startup_summary(app.state, settings)
    yield
    database.close_database()

def connect_modules(state: State) -> None:
    """Conecta batch con prediction"""
    state.batch_archive = None
    if state.storage is not None:
        state.batch_archive = StorageBatchArchive(state.storage)

# Crear la aplicación FastAPI
app = FastAPI(
    title="Fraud Detector API",
    description="Detección de transacciones fraudulentas entrenada con PaySim.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)

# Limitar el tamaño de las peticiones (los CSV)
app.add_middleware(BodySizeLimit, max_bytes=(settings.max_upload_mb + 1) * 1024 * 1024)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

# Incluir todas las rutas
app.include_router(api_router, prefix=API_PREFIX)

# Convertir los errores de validación en respuestas 422
register_error_handlers(app)


@app.get("/", include_in_schema=False)
@app.get("/api", include_in_schema=False)
def root_endpoint():
    """Redirige a la documentación, o al índice si está desactivada"""
    return RedirectResponse(app.docs_url or API_PREFIX)

@app.get(API_PREFIX, tags=["index"])
def index_endpoint(request: Request):
    """Nombre, versión y enlaces de la API"""
    return {
        "name": app.title,
        "version": app.version,
        "docs": f"{str(request.base_url).rstrip('/')}{app.docs_url}" if app.docs_url else None,
        "health": str(request.url_for("health_endpoint")),
    }
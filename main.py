import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.datastructures import State

from app.batch.batch_adapter import BatchFilesCleaner, StorageBatchArchive
from app.model.model_schema import MetricsOut
from app.prediction.prediction_features import AVAILABLE_COLUMNS
from app.prediction.prediction_policy import build_policy
from app.visualization.visualization_sample import load_sample
from config import database, entities  # noqa: F401  (registra las tablas)
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
    # Crear las tablas y poblar la base con los registros iniciales
    with database.startup_lock():
        if database.open_database():
            with database.SessionLocal() as db:
                run_all_seeders(db)
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
    """Conecta batch con prediction y user"""
    state.batch_archive = None
    state.user_data_cleaners = []
    if state.storage is not None:
        state.batch_archive = StorageBatchArchive(state.storage)
        state.user_data_cleaners.append(BatchFilesCleaner(state.storage))


app = FastAPI(
    title="Fraud Detector API",
    description="Detección de transacciones fraudulentas entrenada con PaySim.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(BodySizeLimit, max_bytes=(settings.max_upload_mb + 1) * 1024 * 1024)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=API_PREFIX)


register_error_handlers(app)


@app.get("/", include_in_schema=False)
@app.get("/api", include_in_schema=False)
def root_endpoint():
    """Redirige a la documentación"""
    return RedirectResponse(app.docs_url or "/docs")


@app.get(API_PREFIX, tags=["index"])
def index_endpoint(request: Request):
    """Nombre, versión y enlaces de la API"""
    return {
        "name": app.title,
        "version": app.version,
        "docs": f"{str(request.base_url).rstrip('/')}{app.docs_url}",
        "health": str(request.url_for("health_endpoint")),
    }

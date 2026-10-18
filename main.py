import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.model.model_schema import MetricsOut
from app.prediction.prediction_features import AVAILABLE_COLUMNS
from app.prediction.prediction_policy import build_policy
from app.visualization.visualization_sample import load_sample
from config.create_default_records import create_default_records
from config.database import open_prediction_repository, open_repositories
from config.routes import BATCH_DOWNLOAD_URL, register_routes
from config.settings import settings
from config.startup_summary import log_startup_summary
from utils.model_loader import load_json, load_metrics, load_model
from utils.storage import open_storage

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool, app.state.users, app.state.batches = open_repositories(settings.database_url)
    app.state.predictions = open_prediction_repository(pool)
    create_default_records(app.state.users)
    app.state.storage = open_storage(
        settings.storage_backend,
        local_dir=settings.storage_dir,
        download_url=BATCH_DOWNLOAD_URL,
        supabase_url=settings.supabase_url,
        supabase_secret_key=settings.supabase_secret_key,
        bucket=settings.supabase_bucket,
    )
    app.state.model = load_model(
        settings.model_path,
        settings.model_sha256,
        available_columns=AVAILABLE_COLUMNS,
    )
    app.state.metrics = load_metrics(settings.metrics_path, MetricsOut)
    app.state.policy = build_policy(app.state.metrics, settings.fraud_threshold)
    app.state.experiments = load_json(settings.experiments_path)
    app.state.profile = load_json(settings.profile_path)
    app.state.sample = load_sample(settings.sample_path)
    log_startup_summary(app.state, settings)
    yield
    if pool is not None:
        pool.close()


app = FastAPI(
    title="Fraud Detector API",
    description="Detección de transacciones fraudulentas entrenada con PaySim.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)

register_routes(app)

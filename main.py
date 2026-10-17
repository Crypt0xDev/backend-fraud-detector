import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.model.model_schema import MetricsOut
from app.prediction.prediction_features import AVAILABLE_COLUMNS
from config.create_default_records import create_default_records
from config.database import open_repositories
from config.routes import register_routes
from config.settings import settings
from utils.model_loader import load_metrics, load_model
from utils.storage import open_storage

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool, app.state.users, app.state.batches = open_repositories(settings.database_url)
    create_default_records(app.state.users)
    app.state.storage = open_storage(
        settings.supabase_url, settings.supabase_secret_key, settings.supabase_bucket
    )
    app.state.model = load_model(
        settings.model_path,
        settings.model_sha256,
        available_columns=AVAILABLE_COLUMNS,
    )
    app.state.metrics = load_metrics(settings.metrics_path, MetricsOut)
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
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

register_routes(app)

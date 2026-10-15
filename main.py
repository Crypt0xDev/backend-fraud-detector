import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.model_info.router import router as model_info_router
from app.prediction.router import router as prediction_router
from app.prediction.schemas import Transaction
from app.shared.config import settings
from app.shared.model_loader import load_metrics, load_model

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = load_model(
        settings.model_path,
        settings.model_sha256,
        available_columns=Transaction.model_fields,
    )
    app.state.metrics = load_metrics(settings.metrics_path)
    yield


app = FastAPI(
    title="Fraud Detector API",
    description="Detección de transacciones fraudulentas entrenada con PaySim.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(model_info_router, prefix="/api/v1")
app.include_router(prediction_router, prefix="/api/v1")

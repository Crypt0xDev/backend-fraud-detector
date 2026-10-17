from fastapi import FastAPI

from app.auth.auth_route import router as auth_router
from app.batch.batch_route import router as batch_router
from app.model.model_route import router as model_router
from app.prediction.prediction_route import router as prediction_router

API_PREFIX = "/api/v1"

ROUTERS = [auth_router, batch_router, model_router, prediction_router]


def register_routes(app: FastAPI) -> None:
    for router in ROUTERS:
        app.include_router(router, prefix=API_PREFIX)

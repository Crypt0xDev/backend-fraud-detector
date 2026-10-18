from fastapi import FastAPI

from app.auth.auth_route import router as auth_router
from app.batch.batch_route import DOWNLOAD_PATH
from app.batch.batch_route import router as batch_router
from app.index.index_route import root_router
from app.index.index_route import router as index_router
from app.model.model_route import router as model_router
from app.prediction.prediction_route import router as prediction_router
from app.user.user_route import router as user_router
from app.visualization.visualization_route import router as visualization_router

API_PREFIX = "/api/v1"
BATCH_DOWNLOAD_URL = f"{API_PREFIX}{batch_router.prefix}{DOWNLOAD_PATH}"

ROUTERS = [
    index_router,
    auth_router,
    user_router,
    batch_router,
    model_router,
    prediction_router,
    visualization_router,
]


def register_routes(app: FastAPI) -> None:
    app.include_router(root_router)
    for router in ROUTERS:
        app.include_router(router, prefix=API_PREFIX)

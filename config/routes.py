from fastapi import APIRouter

from app.auth.auth_route import router as auth_router
from app.batch.batch_route import router as batch_router
from app.model.model_route import router as model_router
from app.prediction.prediction_route import router as prediction_router
from app.role.role_route import router as role_router
from app.user.user_route import router as user_router
from app.visualization.visualization_route import router as visualization_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(role_router)
api_router.include_router(batch_router)
api_router.include_router(model_router)
api_router.include_router(prediction_router)
api_router.include_router(visualization_router)
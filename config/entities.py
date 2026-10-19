# Todas las entidades
from app.batch.batch_entity import Batch
from app.module.module_entity import Module, ModulePermission
from app.permission.permission_entity import Permission
from app.prediction.prediction_entity import PredictionRecord
from app.role.role_entity import Role, RolePermission
from app.user.user_entity import User, UserRole

__all__ = [
    "Batch",
    "Module",
    "ModulePermission",
    "Permission",
    "PredictionRecord",
    "Role",
    "RolePermission",
    "User",
    "UserRole",
]

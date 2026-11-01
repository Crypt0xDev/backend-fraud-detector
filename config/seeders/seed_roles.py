import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.module.module_entity import Module, ModulePermission
from app.permission.permission_entity import Permission
from app.role.role_entity import Role, RolePermission
from app.role.role_schema import ANALYST_ROLE

logger = logging.getLogger(__name__)

ANALYST_PERMISSIONS = {
    "lotes": ("ver", "eliminar"),
    "predicciones": ("ver", "crear"),
    "modelo": ("ver",),
    "visualizacion": ("ver",),
}

def seed_roles(db: Session) -> None:
    """Crea el rol Analista si no existe"""
    if db.scalars(select(Role).where(Role.name == ANALYST_ROLE)).first():
        logger.debug("ℹ️  Rol %s: ya existe", ANALYST_ROLE)
        return

    role = Role(
        name=ANALYST_ROLE,
        description="Analiza transacciones y CSV y consulta sus resultados",
    )
    db.add(role)
    db.flush()
    for code, actions in ANALYST_PERMISSIONS.items():
        module_permissions = db.scalars(
            select(ModulePermission)
            .join(Module)
            .join(Permission)
            .where(Module.code == code, Permission.name.in_(actions))
        ).all()
        for module_permission in module_permissions:
            db.add(
                RolePermission(
                    role_id=role.id, module_permission_id=module_permission.id
                )
            )
    db.commit()
    logger.info("✅ Rol %s creado", ANALYST_ROLE)

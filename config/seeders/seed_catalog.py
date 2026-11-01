import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.module.module_entity import Module, ModulePermission
from app.permission.permission_entity import Permission

logger = logging.getLogger(__name__)

PERMISSIONS = ("ver", "crear", "editar", "eliminar")

# Módulos del panel: (code, nombre, icono, ruta, acciones). No cambiar los code
MODULES = (
    ("lotes", "Lotes", "folder", "/lotes", ("ver", "eliminar")),
    ("predicciones", "Predicciones", "activity", "/predicciones", ("ver", "crear")),
    ("modelo", "Modelo", "cpu", "/modelo", ("ver", "editar")),
    ("visualizacion", "Visualización", "chart", "/visualizacion", ("ver",)),
)

def seed_catalog(db: Session) -> None:
    """Crea los permisos y los módulos si todavía no existen"""
    inserted = 0

    permissions: dict[str, Permission] = {}
    for name in PERMISSIONS:
        permission = db.scalars(select(Permission).where(Permission.name == name)).first()
        if not permission:
            permission = Permission(name=name)
            db.add(permission)
            db.flush()
            inserted += 1
        permissions[name] = permission

    for code, name, icon, path, actions in MODULES:
        module = db.scalars(select(Module).where(Module.code == code)).first()
        if not module:
            module = Module(code=code, name=name, icon=icon, path=path, is_parent=False)
            db.add(module)
            db.flush()
            inserted += 1
        for action in actions:
            exists = db.scalars(
                select(ModulePermission).where(
                    ModulePermission.module_id == module.id,
                    ModulePermission.permission_id == permissions[action].id,
                )
            ).first()
            if not exists:
                db.add(
                    ModulePermission(
                        module_id=module.id, permission_id=permissions[action].id
                    )
                )
                inserted += 1

    db.commit()
    if inserted:
        logger.info("✅ Catálogo: %s registro(s) insertado(s)", inserted)
    else:
        logger.debug("ℹ️  Catálogo: todos los registros ya existen")

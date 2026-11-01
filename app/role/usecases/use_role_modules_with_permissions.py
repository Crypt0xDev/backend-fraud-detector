from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.module.module_entity import Module, ModulePermission
from app.role.role_schema import ModuleTreeResponse


def execute(db: Session) -> list[ModuleTreeResponse]:
    # unique(): el joinedload de una lista repite el módulo por cada permiso
    modules = db.scalars(select(Module).options(joinedload(Module.module_permissions).joinedload(ModulePermission.permission)).order_by(Module.id.asc())).unique().all()
    return ModuleTreeResponse.build_tree(list(modules))

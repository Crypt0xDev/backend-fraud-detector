from sqlalchemy.orm import Session, joinedload

from app.module.module_entity import Module, ModulePermission
from app.role.role_schema import ModuleTreeResponse


def execute(db: Session) -> list[ModuleTreeResponse]:
    modules = (
        db.query(Module)
        .options(
            joinedload(Module.module_permissions).joinedload(
                ModulePermission.permission
            )
        )
        .order_by(Module.id.asc())
        .all()
    )
    return ModuleTreeResponse.build_tree(modules)

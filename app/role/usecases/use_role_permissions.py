from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.module.module_entity import ModulePermission
from app.role.role_entity import Role, RolePermission
from app.role.role_schema import SchemaRoleResponse
from utils.errors import ConflictError, InvalidRequestError, NotFoundError


def validate_module_permission_ids(db: Session, ids: list[int]) -> None:
    """Revisa que existan todos los permisos enviados"""
    if not ids:
        return
    found = {
        row.id
        for row in db.query(ModulePermission.id).filter(ModulePermission.id.in_(ids))
    }
    missing = sorted(set(ids) - found)
    if missing:
        raise InvalidRequestError(
            f"Los siguientes IDs de permisos de módulo no existen: {missing}"
        )


def role_not_found() -> NotFoundError:
    return NotFoundError("Rol no encontrado")


def with_permissions():
    """Carga los permisos de los roles en pocas consultas, no una por rol"""
    return selectinload(Role.role_permissions).options(
        joinedload(RolePermission.module_permission).options(
            joinedload(ModulePermission.module),
            joinedload(ModulePermission.permission),
        )
    )


def commit_unique_name(db: Session, name: str) -> None:
    """Guarda; si otro rol ya tiene ese nombre da 409 (lo decide el UNIQUE de la base)"""
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if db.query(Role.id).filter(Role.name == name).first() is None:
            raise
        raise ConflictError("Ya existe un rol con ese nombre") from error


def to_response(role: Role) -> SchemaRoleResponse:
    permissions: dict[str, list[str]] = {}
    for role_permission in role.role_permissions:
        module_permission = role_permission.module_permission
        permissions.setdefault(module_permission.module.code, []).append(
            module_permission.permission.name
        )
    return SchemaRoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        created_at=role.created_at,
        updated_at=role.updated_at,
        module_permission_ids=sorted(
            rp.module_permission_id for rp in role.role_permissions
        ),
        permissions=permissions,
    )

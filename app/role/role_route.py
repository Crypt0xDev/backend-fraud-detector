# fastapi
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

# dependencias
from app.auth.auth_dependency import get_current_root

# esquemas
from app.role.role_schema import (
    ModuleTreeResponse,
    SchemaRoleCreate,
    SchemaRoleResponse,
    SchemaRoleUpdate,
)

# casos de uso
from app.role.usecases.use_role_create import execute as create_role_execute
from app.role.usecases.use_role_delete import execute as delete_role_execute
from app.role.usecases.use_role_list import execute as list_role_execute
from app.role.usecases.use_role_modules_with_permissions import (
    execute as modules_with_permissions_role_execute,
)
from app.role.usecases.use_role_update import execute as update_role_execute
from app.role.usecases.use_role_view import execute as view_role_execute

# entidades
from app.user.user_entity import User
from config.database import get_db

router = APIRouter(prefix="/roles", tags=["roles"])


def not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado"
    )


@router.get("/modules-with-permissions", response_model=list[ModuleTreeResponse])
def modules_with_permissions_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_root),
):
    """Módulos con sus permisos, para marcar las casillas al crear un rol"""
    return modules_with_permissions_role_execute(db=db, current_user=current_user)


@router.post("", response_model=SchemaRoleResponse, status_code=status.HTTP_201_CREATED)
def create_role_endpoint(
    role: SchemaRoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_root),
):
    """Crear un rol con sus permisos. Solo el root"""
    return create_role_execute(db=db, current_user=current_user, role=role)


@router.get("", response_model=list[SchemaRoleResponse])
def list_role_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_root),
):
    """Listar los roles con sus permisos"""
    return list_role_execute(db=db, current_user=current_user)


@router.get("/{role_id}", response_model=SchemaRoleResponse)
def view_role_endpoint(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_root),
):
    """Ver un rol"""
    role = view_role_execute(db=db, current_user=current_user, role_id=role_id)
    if role is None:
        raise not_found()
    return role


@router.put("/{role_id}", response_model=SchemaRoleResponse)
def update_role_endpoint(
    role_id: int,
    role_data: SchemaRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_root),
):
    """Actualizar un rol. Se quedan solo los permisos que se envían"""
    role = update_role_execute(
        db=db, current_user=current_user, role_id=role_id, role_data=role_data
    )
    if role is None:
        raise not_found()
    return role


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        204: {"description": "Rol eliminado correctamente"},
        404: {"description": "Rol no encontrado"},
        409: {"description": "El rol está asignado a usuarios"},
    },
)
def delete_role_endpoint(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_root),
):
    """Eliminar un rol que ningún usuario tenga"""
    if not delete_role_execute(db=db, current_user=current_user, role_id=role_id):
        raise not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

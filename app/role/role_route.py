# fastapi
from fastapi import APIRouter, Depends, Response, status
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
from config.database import get_db

# Todo el módulo es solo para el root
router = APIRouter(
    prefix="/roles", tags=["roles"], dependencies=[Depends(get_current_root)]
)


@router.get("/modules-with-permissions", response_model=list[ModuleTreeResponse])
def modules_with_permissions_endpoint(db: Session = Depends(get_db)):
    """Módulos con sus permisos, para marcar las casillas al crear un rol"""
    return modules_with_permissions_role_execute(db=db)


@router.post("", response_model=SchemaRoleResponse, status_code=status.HTTP_201_CREATED)
def create_role_endpoint(role: SchemaRoleCreate, db: Session = Depends(get_db)):
    """Crear un rol con sus permisos. Solo el root"""
    return create_role_execute(db=db, role=role)


@router.get("", response_model=list[SchemaRoleResponse])
def list_role_endpoint(db: Session = Depends(get_db)):
    """Listar los roles con sus permisos"""
    return list_role_execute(db=db)


@router.get("/{role_id}", response_model=SchemaRoleResponse)
def view_role_endpoint(role_id: int, db: Session = Depends(get_db)):
    """Ver un rol"""
    return view_role_execute(db=db, role_id=role_id)


@router.put("/{role_id}", response_model=SchemaRoleResponse)
def update_role_endpoint(
    role_id: int, role_data: SchemaRoleUpdate, db: Session = Depends(get_db)
):
    """Actualizar un rol. Se quedan solo los permisos que se envían"""
    return update_role_execute(db=db, role_id=role_id, role_data=role_data)


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
def delete_role_endpoint(role_id: int, db: Session = Depends(get_db)):
    """Eliminar un rol que ningún usuario tenga"""
    delete_role_execute(db=db, role_id=role_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

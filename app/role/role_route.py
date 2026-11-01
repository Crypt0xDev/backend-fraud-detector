# fastapi
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

# dependencias
from config.database import get_db
from app.auth.auth_dependency import get_current_root

# casos de uso
from app.role.usecases.use_role_create import execute as create_role_execute
from app.role.usecases.use_role_list import execute as list_role_execute
from app.role.usecases.use_role_view import execute as view_role_execute
from app.role.usecases.use_role_update import execute as update_role_execute
from app.role.usecases.use_role_delete import execute as delete_role_execute
from app.role.usecases.use_role_modules_with_permissions import execute as modules_with_permissions_role_execute

# esquemas
from app.role.role_schema import SchemaRoleCreate, SchemaRoleUpdate, SchemaRoleResponse, ModuleTreeResponse

# Todas las rutas de roles son solo para el root
router = APIRouter(prefix="/roles", tags=["roles"], dependencies=[Depends(get_current_root)])


def not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")


@router.get("/modules-with-permissions", response_model=list[ModuleTreeResponse])
def modules_with_permissions_endpoint(db: Session = Depends(get_db)):
    """Módulos con sus permisos, para marcar las casillas al crear un rol"""
    return modules_with_permissions_role_execute(db=db)

@router.post("", status_code=status.HTTP_201_CREATED, response_class=Response)
def create_role_endpoint(
    role: SchemaRoleCreate,
    db: Session = Depends(get_db),
):
    """
    Crea un rol con sus permisos.
    Solo el root puede ejecutar este endpoint.
    """
    create_role_execute(db=db, role=role)
    return Response(status_code=status.HTTP_201_CREATED)

@router.get("", response_model=list[SchemaRoleResponse])
def list_role_endpoint(db: Session = Depends(get_db)):
    """Listar los roles con sus permisos"""
    return list_role_execute(db=db)

@router.get("/{role_id}", response_model=SchemaRoleResponse)
def view_role_endpoint(
    role_id: int,
    db: Session = Depends(get_db),
):
    """Ver un rol"""
    role = view_role_execute(db=db, role_id=role_id)
    if role is None:
        raise not_found()
    return role

@router.put("/{role_id}", response_model=SchemaRoleResponse)
def update_role_endpoint(
    role_id: int,
    role_data: SchemaRoleUpdate,
    db: Session = Depends(get_db),
):
    """Actualizar un rol. Se quedan solo los permisos que se envían"""
    role = update_role_execute(db=db, role_id=role_id, role_data=role_data)
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
        409: {"description": "El rol está asignado a usuarios o es el rol por defecto"},
    },
)
def delete_role_endpoint(
    role_id: int,
    db: Session = Depends(get_db),
):
    """Eliminar un rol que ningún usuario tenga"""
    if not delete_role_execute(db=db, role_id=role_id):
        raise not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

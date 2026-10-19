# fastapi
from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

# dependencias
from app.auth.auth_dependency import get_current_root, get_current_user

# casos de uso
from app.user.usecases.use_user_change_password import (
    execute as change_password_user_execute,
)
from app.user.usecases.use_user_create import execute as create_user_execute
from app.user.usecases.use_user_delete import execute as delete_user_execute
from app.user.usecases.use_user_disable import execute as disable_user_execute
from app.user.usecases.use_user_enable import execute as enable_user_execute
from app.user.usecases.use_user_list import execute as list_user_execute
from app.user.usecases.use_user_update import execute as update_user_execute
from app.user.usecases.use_user_view import execute as view_user_execute

# entidades
from app.user.user_entity import User

# esquemas
from app.user.user_schema import (
    SchemaChangePassword,
    SchemaCreate,
    SchemaResponse,
    SchemaUpdate,
)
from config.database import get_db

router = APIRouter(prefix="/users", tags=["users"])

# Para los endpoints que solo puede usar el root y no necesitan saber quién es
ROOT_ONLY = [Depends(get_current_root)]


@router.post(
    "",
    response_model=SchemaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=ROOT_ONLY,
)
def create_user_endpoint(user: SchemaCreate, db: Session = Depends(get_db)):
    """Crear un usuario. Solo el root"""
    return create_user_execute(db=db, user=user)


@router.get("", response_model=list[SchemaResponse], dependencies=ROOT_ONLY)
def list_user_endpoint(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Listar todos los usuarios"""
    return list_user_execute(db=db, skip=skip, limit=limit)


@router.patch(
    "/me/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def change_password_endpoint(
    data: SchemaChangePassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cambiar la contraseña del usuario que inició sesión; cierra sus sesiones"""
    change_password_user_execute(db=db, current_user=current_user, data=data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{username}", response_model=SchemaResponse, dependencies=ROOT_ONLY)
def view_user_endpoint(username: str, db: Session = Depends(get_db)):
    """Ver un usuario específico"""
    return view_user_execute(db=db, username=username)


@router.patch("/{username}", response_model=SchemaResponse)
def update_user_endpoint(
    username: str,
    user_data: SchemaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_root),
):
    """Actualizar el rol o la contraseña de un usuario"""
    return update_user_execute(
        db=db, current_user=current_user, username=username, user_data=user_data
    )


@router.delete(
    "/{username}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        204: {"description": "Usuario eliminado correctamente"},
        404: {"description": "Usuario no encontrado"},
    },
)
def delete_user_endpoint(
    username: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_root),
):
    """Eliminar un usuario junto con sus lotes, predicciones y archivos"""
    delete_user_execute(
        db=db,
        current_user=current_user,
        username=username,
        cleaners=request.app.state.user_data_cleaners,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{username}/enable",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=ROOT_ONLY,
)
def enable_user_endpoint(username: str, db: Session = Depends(get_db)):
    """Habilitar un usuario"""
    enable_user_execute(db=db, username=username)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{username}/disable",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def disable_user_endpoint(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_root),
):
    """Deshabilitar un usuario: no podrá iniciar sesión hasta que se habilite"""
    disable_user_execute(db=db, current_user=current_user, username=username)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

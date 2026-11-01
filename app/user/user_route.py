# fastapi
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

# dependencias
from config.database import get_db
from app.auth.auth_dependency import get_current_root, get_current_user

# casos de uso
from app.user.usecases.use_user_create import execute as create_user_execute
from app.user.usecases.use_user_list import execute as list_user_execute
from app.user.usecases.use_user_view import execute as view_user_execute
from app.user.usecases.use_user_update import execute as update_user_execute
from app.user.usecases.use_user_delete import execute as delete_user_execute
from app.user.usecases.use_user_enable import execute as enable_user_execute
from app.user.usecases.use_user_disable import execute as disable_user_execute
from app.user.usecases.use_user_change_password import execute as change_password_user_execute

# entidades
from app.user.user_entity import User

# esquemas
from app.user.user_schema import SchemaCreate, SchemaUpdate, SchemaResponse, SchemaChangePassword, UserPageOut

router = APIRouter(prefix="/users", tags=["users"])


def not_found(detail: str = "Usuario no encontrado") -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.post("", status_code=status.HTTP_201_CREATED, response_class=Response, dependencies=[Depends(get_current_root)])
def create_user_endpoint(
    user: SchemaCreate,
    db: Session = Depends(get_db),
):
    """
    Crea un usuario del sistema con uno o más roles.
    Solo el root puede ejecutar este endpoint.
    """
    create_user_execute(db=db, user=user)
    return Response(status_code=status.HTTP_201_CREATED)

@router.get("", response_model=UserPageOut, dependencies=[Depends(get_current_root)])
def list_user_endpoint(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Listar los usuarios, de a una página"""
    return list_user_execute(db=db, page=page, page_size=page_size)


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

@router.get("/{username}", response_model=SchemaResponse, dependencies=[Depends(get_current_root)])
def view_user_endpoint(
    username: str,
    db: Session = Depends(get_db),
):
    """Ver un usuario específico"""
    user = view_user_execute(db=db, username=username)
    if user is None:
        raise not_found()
    return user

@router.patch("/{username}", response_model=SchemaResponse)
def update_user_endpoint(
    username: str,
    user_data: SchemaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_root),
):
    """Actualizar el rol o la contraseña de un usuario"""
    user = update_user_execute(db=db, current_user=current_user, username=username, user_data=user_data)
    if user is None:
        raise not_found()
    return user

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_root),
):
    """Eliminar un usuario; sus lotes y predicciones se quedan guardados"""
    if not delete_user_execute(db=db, current_user=current_user, username=username):
        raise not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.patch(
    "/{username}/enable",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(get_current_root)],
)
def enable_user_endpoint(
    username: str,
    db: Session = Depends(get_db),
):
    """Habilitar un usuario"""
    if not enable_user_execute(db=db, username=username):
        raise not_found("Usuario no encontrado o ya está habilitado")
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
    if not disable_user_execute(db=db, current_user=current_user, username=username):
        raise not_found("Usuario no encontrado o ya está deshabilitado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

from app.batch.batch_repository import BatchRepository
from app.batch.batch_storage import object_paths
from app.user.usecases.use_user_update import (
    ProtectedUserError,
    ensure_exists,
    ensure_not_last_admin,
)
from app.user.user_repository import UserRepository
from utils.storage import FileStorage


def delete_user(
    users: UserRepository,
    batches: BatchRepository | None,
    storage: FileStorage | None,
    username: str,
    *,
    acting_admin: str,
) -> None:
    """Borra el usuario, sus lotes (en cascada en la base) y los archivos de esos lotes."""
    ensure_exists(users, username)
    if username == acting_admin:
        raise ProtectedUserError("No puedes borrar tu propio usuario")
    ensure_not_last_admin(users, username)
    if batches is not None and storage is not None:
        paths = [
            path
            for batch_id in batches.ids(username)
            for path in object_paths(batch_id)
        ]
        if paths:
            storage.delete(paths)
    users.delete(username)

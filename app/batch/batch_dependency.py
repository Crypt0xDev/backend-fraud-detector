from fastapi import HTTPException, Request, status

from utils.storage import FileStorage


def get_storage(request: Request) -> FileStorage:
    if request.app.state.storage is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El historial de lotes no está configurado",
        )
    return request.app.state.storage

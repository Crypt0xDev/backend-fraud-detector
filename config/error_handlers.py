import math
from collections.abc import Sequence
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from utils.errors import (
    AuthenticationError,
    ConflictError,
    DomainError,
    ForbiddenError,
    InvalidDataError,
    InvalidRequestError,
    InvalidRowsError,
    NotFoundError,
    RateLimitedError,
    StorageFailureError,
    UnavailableError,
)

# Código HTTP de cada error de los casos de uso
STATUS_CODES: dict[type[DomainError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    ForbiddenError: status.HTTP_403_FORBIDDEN,
    InvalidRequestError: status.HTTP_400_BAD_REQUEST,
    InvalidDataError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    InvalidRowsError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    RateLimitedError: status.HTTP_429_TOO_MANY_REQUESTS,
    UnavailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
    StorageFailureError: status.HTTP_502_BAD_GATEWAY,
}


def json_safe(value: Any) -> Any:
    """Cambia Infinity y NaN por texto: JSON no los admite y el 422 daba error 500"""
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [json_safe(item) for item in value]
    return value


def validation_errors_response(errors: Sequence[Any]) -> JSONResponse:
    """El mismo 422 de FastAPI, aunque la entrada traiga números no finitos"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": json_safe(jsonable_encoder(errors))},
    )


# Starlette pide que los manejadores reciban Exception; se revisa el tipo adentro
async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc
    return validation_errors_response(exc.errors())


async def domain_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, DomainError):
        raise exc
    if isinstance(exc, InvalidRowsError):
        return validation_errors_response(exc.errors)
    status_code = next(
        (code for kind, code in STATUS_CODES.items() if isinstance(exc, kind)),
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    headers: dict[str, str] = {}
    if isinstance(exc, AuthenticationError):
        headers["WWW-Authenticate"] = "Bearer"
    retry_after = getattr(exc, "retry_after", None)
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    return JSONResponse(
        status_code=status_code, content={"detail": exc.detail}, headers=headers
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(DomainError, domain_exception_handler)

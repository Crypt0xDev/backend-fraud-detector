import math
from collections.abc import Sequence
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


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
async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc
    return validation_errors_response(exc.errors())


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

from fastapi import HTTPException, status
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

TOO_LARGE = "La petición supera el tamaño máximo permitido"

class BodySizeLimit:
    """Corta las peticiones con un cuerpo mayor que max_bytes.
    FastAPI lee el cuerpo antes de revisar la sesión, así que sin esto cualquiera
    podía mandar cuerpos enormes sin iniciar sesión
    """

    def __init__(self, app: ASGIApp, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        length = dict(scope["headers"]).get(b"content-length")
        if length is not None and (
            not length.isdigit() or int(length) > self.max_bytes
        ):
            response = JSONResponse(
                {"detail": TOO_LARGE}, status_code=status.HTTP_413_CONTENT_TOO_LARGE
            )
            await response(scope, receive, send)
            return
        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=TOO_LARGE
                    )
            return message

        await self.app(scope, limited_receive, send)

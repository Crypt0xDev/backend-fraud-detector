import threading
import time
from collections import defaultdict, deque
from typing import Annotated

from fastapi import Depends, HTTPException, status

from config.settings import settings
from utils.auth import get_current_user

WINDOW_SECONDS = 60.0


class RateLimiter:
    """Ventana deslizante en memoria por usuario. Suficiente para una sola instancia;
    con varias réplicas habría que moverlo a Redis o al proxy."""

    def __init__(self) -> None:
        self.hits: dict[str, deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key: str, limit: int, now: float | None = None) -> bool:
        if limit <= 0:
            return True
        now = time.monotonic() if now is None else now
        with self.lock:
            hits = self.hits[key]
            while hits and now - hits[0] >= WINDOW_SECONDS:
                hits.popleft()
            if len(hits) >= limit:
                return False
            hits.append(now)
            return True


limiter = RateLimiter()


def rate_limit(username: Annotated[str, Depends(get_current_user)]) -> None:
    if not limiter.allow(username, settings.rate_limit_per_minute):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiadas solicitudes. Espera un minuto e inténtalo de nuevo.",
            headers={"Retry-After": str(int(WINDOW_SECONDS))},
        )


RateLimited = Depends(rate_limit)

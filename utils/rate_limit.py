import threading
import time
from collections import defaultdict, deque

WINDOW_SECONDS = 60.0

class RateLimiter:
    """Límite de peticiones por minuto de cada usuario (en memoria)"""

    def __init__(self) -> None:
        self.hits: dict[str, deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()
        self.last_sweep = 0.0

    def allow(self, key: str, limit: int, now: float | None = None) -> bool:
        if limit <= 0:
            return True
        now = time.monotonic() if now is None else now
        with self.lock:
            if now - self.last_sweep >= WINDOW_SECONDS:
                self._sweep(now)
            hits = self.hits[key]
            while hits and now - hits[0] >= WINDOW_SECONDS:
                hits.popleft()
            if len(hits) >= limit:
                return False
            hits.append(now)
            return True

    def _sweep(self, now: float) -> None:
        """Olvida las claves sin peticiones en el último minuto, para no crecer sin fin"""
        expired = [
            key
            for key, hits in self.hits.items()
            if not hits or now - hits[-1] >= WINDOW_SECONDS
        ]
        for key in expired:
            del self.hits[key]
        self.last_sweep = now

limiter = RateLimiter()
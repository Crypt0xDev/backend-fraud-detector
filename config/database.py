import logging

from psycopg_pool import ConnectionPool

from app.batch.batch_repository import BatchRepository
from app.prediction.prediction_repository import PredictionRepository
from app.user.user_repository import UserRepository

logger = logging.getLogger(__name__)


def open_pool(database_url: str | None) -> ConnectionPool | None:
    if not database_url:
        logger.warning(
            "DATABASE_URL no está definido: login e historial no estarán disponibles"
        )
        return None

    pool = ConnectionPool(
        database_url,
        min_size=1,
        max_size=5,
        open=False,
        kwargs={"autocommit": True, "prepare_threshold": None},
    )
    pool.open()
    return pool


def open_repositories(
    database_url: str | None,
) -> tuple[ConnectionPool | None, UserRepository | None, BatchRepository | None]:
    pool = open_pool(database_url)
    if pool is None:
        return None, None, None
    users, batches = UserRepository(pool), BatchRepository(pool)
    try:
        users.init_schema()
        batches.init_schema()
    except Exception:
        logger.exception("No se pudieron preparar las tablas")
    return pool, users, batches


def open_prediction_repository(
    pool: ConnectionPool | None,
) -> PredictionRepository | None:
    if pool is None:
        return None
    predictions = PredictionRepository(pool)
    try:
        predictions.init_schema()
    except Exception:
        logger.exception("No se pudo preparar la tabla de predicciones")
    return predictions

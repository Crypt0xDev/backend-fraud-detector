import logging
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import HTTPException, status
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config.settings import settings

logger = logging.getLogger(__name__)

# Número cualquiera que identifica el bloqueo del arranque en PostgreSQL
STARTUP_LOCK_KEY = 7_465_011


def sqlalchemy_url(url: str) -> str:
    """Cambia la URL para que SQLAlchemy use psycopg 3"""
    for scheme in ("postgresql://", "postgres://"):
        if url.startswith(scheme):
            return "postgresql+psycopg://" + url.removeprefix(scheme)
    return url


def make_engine(database_url: str) -> Engine:
    return create_engine(
        sqlalchemy_url(database_url),
        pool_size=settings.db_pool_size,
        pool_pre_ping=True,
        connect_args={"prepare_threshold": None},
    )


# Conexión a PostgreSQL
engine = make_engine(settings.database_url) if settings.database_url else None

# Crear una sesión local
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


# Base para las entidades
class BaseModel(DeclarativeBase):
    pass


# Obtener una sesión de DB
def get_db() -> Iterator[Session]:
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La base de datos no está configurada",
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(bind: Engine) -> None:
    """Crea las tablas que falten."""
    BaseModel.metadata.create_all(bind)
    if bind.dialect.name != "postgresql":
        return
    with bind.begin() as conn:
        for table in BaseModel.metadata.sorted_tables:
            for statement in table.info.get("upgrades", ()):
                conn.execute(text(statement))


@contextmanager
def startup_lock() -> Iterator[None]:
    """Con varios workers, uno prepara las tablas y los registros y los demás esperan.

    Es un bloqueo de transacción porque el pooler de Supabase (modo transacción)
    no garantiza que un bloqueo de sesión se libere en la misma conexión
    """
    if engine is None or engine.dialect.name != "postgresql":
        yield
        return
    with engine.connect() as conn, conn.begin():
        conn.execute(
            text("SELECT pg_advisory_xact_lock(:key)"), {"key": STARTUP_LOCK_KEY}
        )
        yield


def open_database() -> bool:
    """Prepara las tablas al arrancar"""
    if engine is None:
        logger.warning(
            "DATABASE_URL no está definido: login e historial no estarán disponibles"
        )
        return False
    try:
        init_db(engine)
    except Exception:
        logger.exception("No se pudieron preparar las tablas")
        return False
    return True


def close_database() -> None:
    if engine is not None:
        engine.dispose()

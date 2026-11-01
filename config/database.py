import hashlib
import logging
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import HTTPException, status
from sqlalchemy import Connection, Engine, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config.settings import settings

logger = logging.getLogger(__name__)

STARTUP_LOCK_KEY = 7_465_011

# Tabla con los upgrades ya aplicados, para no repetirlos en cada arranque
UPGRADES_TABLE = "schema_upgrades"

# Segundos para conectar; sin esto /health se queda colgado si la base no responde
CONNECT_TIMEOUT_SECONDS = 5

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
        connect_args={"prepare_threshold": None, "connect_timeout": CONNECT_TIMEOUT_SECONDS},
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
        apply_upgrades(conn)

def apply_upgrades(conn: Connection) -> None:
    """Ejecuta una sola vez cada sentencia de los upgrades; se reconocen por su hash.
    Cambiar el texto de una sentencia la vuelve a ejecutar, así que deben poder repetirse"""
    conn.execute(text(
        f"CREATE TABLE IF NOT EXISTS {UPGRADES_TABLE} ("
        "id TEXT PRIMARY KEY, statement TEXT NOT NULL, "
        "applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
    ))
    conn.execute(text(f"ALTER TABLE {UPGRADES_TABLE} ENABLE ROW LEVEL SECURITY"))
    applied = set(conn.execute(text(f"SELECT id FROM {UPGRADES_TABLE}")).scalars())
    for table in BaseModel.metadata.sorted_tables:
        for statement in table.info.get("upgrades", ()):
            key = hashlib.sha256(statement.encode()).hexdigest()
            if key in applied:
                continue
            conn.execute(text(statement))
            conn.execute(
                text(f"INSERT INTO {UPGRADES_TABLE} (id, statement) VALUES (:id, :statement)"),
                {"id": key, "statement": statement},
            )
            applied.add(key)

def check_database() -> bool | None:
    """None si no hay base configurada; si no, si responde a un SELECT 1"""
    if engine is None:
        return None
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        logger.warning("La base de datos no responde", exc_info=True)
        return False
    return True

@contextmanager
def startup_lock() -> Iterator[None]:
    """Bloquea el arranque para que no se creen varias veces las tablas y los roles"""
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
            "DATABASE_URL no está definido, no se puede preparar la base de datos"
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

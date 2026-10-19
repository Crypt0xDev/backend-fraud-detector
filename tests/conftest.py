"""Pruebas contra la app real: base de datos aislada, disco temporal y el modelo real.

Por defecto usa SQLite en memoria. Con TEST_DATABASE_URL usa esa base de PostgreSQL:
se BORRAN todas sus tablas en cada prueba, así que nunca apuntes a una base real.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

import main
from config import database
from config.settings import settings
from utils.rate_limit import limiter

ADMIN = ("admin", "admin-pass-123")
ANALYST = ("analyst", "analyst-pass-123")

TRANSACTION = {
    "step": 1,
    "type": "TRANSFER",
    "amount": 181.0,
    "nameOrig": "C1305486145",
    "oldbalanceOrg": 181.0,
    "newbalanceOrig": 0.0,
    "nameDest": "C553264065",
    "oldbalanceDest": 0.0,
    "newbalanceDest": 0.0,
}

CSV_HEADER = (
    "step,type,amount,nameOrig,oldbalanceOrg,newbalanceOrig,nameDest,"
    "oldbalanceDest,newbalanceDest,isFraud"
)
CSV_ROW = "1,TRANSFER,181.0,C1305486145,181.0,0.0,C553264065,0.0,0.0,1"


def sqlite_engine(path):
    # En archivo y no en memoria: al apagarse, la app hace engine.dispose()
    engine = create_engine(
        f"sqlite+pysqlite:///{path}", connect_args={"check_same_thread": False}
    )

    # Sin esto SQLite ignora ON DELETE CASCADE
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    return engine


@pytest.fixture(scope="session")
def engine(tmp_path_factory):
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        engine = database.make_engine(url)
    else:
        engine = sqlite_engine(tmp_path_factory.mktemp("db") / "test.sqlite")
    yield engine
    engine.dispose()


@pytest.fixture
def is_postgres(engine) -> bool:
    return engine.dialect.name == "postgresql"


@pytest.fixture
def client(engine, monkeypatch, tmp_path):
    database.BaseModel.metadata.drop_all(engine)
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(
        database,
        "SessionLocal",
        sessionmaker(bind=engine, autoflush=False, expire_on_commit=False),
    )
    for name, value in {
        "api_public_url": "http://testserver",
        "storage_backend": "local",
        "storage_dir": tmp_path,
        "admin_username": ADMIN[0],
        "admin_password": ADMIN[1],
        "user_username": ANALYST[0],
        "user_password": ANALYST[1],
        "rate_limit_per_minute": 120,
    }.items():
        monkeypatch.setattr(settings, name, value)
    limiter.hits.clear()
    with TestClient(main.app) as test_client:
        yield test_client
    limiter.hits.clear()


def login(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login", data={"username": username, "password": password}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def admin(client) -> dict[str, str]:
    return login(client, *ADMIN)


@pytest.fixture
def analyst(client) -> dict[str, str]:
    return login(client, *ANALYST)


@pytest.fixture
def make_user(client, admin):
    """Crea un usuario con el rol Analista y devuelve sus cabeceras"""

    def create(username: str, password: str = "other-pass-123", **extra):
        response = client.post(
            "/api/v1/users",
            json={"username": username, "password": password, **extra},
            headers=admin,
        )
        assert response.status_code == 201, response.text
        return login(client, username, password)

    return create

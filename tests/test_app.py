from fastapi.testclient import TestClient

import main
from config import database
from utils.rate_limit import RateLimiter


def test_rutas_publicas_y_openapi(client):
    spec = client.get("/openapi.json").json()
    public = sorted(
        f"{method.upper()} {path}"
        for path, operations in spec["paths"].items()
        for method, operation in operations.items()
        if not operation.get("security")
    )
    assert public == [
        "GET /api/v1",
        "GET /api/v1/batches/download",
        "GET /api/v1/health",
        "POST /api/v1/auth/login",
    ]
    assert client.get("/api/v1/health").json() == {
        "status": "ok",
        "model_loaded": True,
        "metrics_loaded": True,
    }


def test_endpoints_del_modelo(client, analyst):
    assert client.get("/api/v1/metrics").status_code == 401
    metrics = client.get("/api/v1/metrics", headers=analyst)
    assert metrics.status_code == 200
    assert metrics.json()["version"] == "v001"
    info = client.get("/api/v1/model/info", headers=analyst).json()
    assert info["loaded"] is True
    experiments = client.get("/api/v1/experiments", headers=analyst).json()
    assert experiments["experiments"]
    version = experiments["experiments"][0]["version"]
    assert (
        client.get(f"/api/v1/experiments/{version}", headers=analyst).status_code == 200
    )
    assert client.get("/api/v1/experiments/nada", headers=analyst).status_code == 404
    assert client.get("/api/v1/dataset/profile", headers=analyst).status_code == 200


def test_reiniciar_no_duplica_los_registros_iniciales(client, engine):
    from sqlalchemy import func, select

    from app.module.module_entity import ModulePermission
    from app.role.role_entity import Role

    def count(model):
        with database.SessionLocal() as db:
            return db.scalar(select(func.count()).select_from(model))

    before = (count(Role), count(ModulePermission))
    with TestClient(main.app):
        pass
    assert (count(Role), count(ModulePermission)) == before


def test_rate_limiter_olvida_las_claves_viejas():
    limiter = RateLimiter()
    for i in range(1000):
        assert limiter.allow(f"login:u{i}", 10, now=0)
    limiter.allow("otra", 10, now=120)
    assert set(limiter.hits) == {"otra"}


def test_un_solo_worker_prepara_la_base_a_la_vez(client, is_postgres):
    import threading

    import pytest

    if not is_postgres:
        pytest.skip("El bloqueo solo existe en PostgreSQL")
    order: list[str] = []
    entered = threading.Event()
    release = threading.Event()

    def first():
        with database.startup_lock():
            order.append("primero entra")
            entered.set()
            release.wait(5)
            order.append("primero sale")

    def second():
        entered.wait(5)
        with database.startup_lock():
            order.append("segundo entra")

    threads = [threading.Thread(target=first), threading.Thread(target=second)]
    for thread in threads:
        thread.start()
    entered.wait(5)
    threads[1].join(timeout=0.5)
    assert threads[1].is_alive(), "el segundo debía esperar"
    release.set()
    for thread in threads:
        thread.join(timeout=5)
    assert order == ["primero entra", "primero sale", "segundo entra"]

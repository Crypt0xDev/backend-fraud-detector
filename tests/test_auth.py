import pytest

import main
from config.settings import settings
from tests.factories import make_transaction
from utils.password import hash_password, verify_password
from utils.token import create_token


@pytest.fixture
def client(client_with_model_path, pipeline_path):
    with client_with_model_path(pipeline_path, authenticated=False) as client:
        client.app.state.users.save("ana", hash_password("secreta123"))
        yield client


def login(client, username="ana", password="secreta123"):
    return client.post(
        "/api/v1/auth/login", data={"username": username, "password": password}
    )


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_password_hash_roundtrip():
    stored = hash_password("secreta123")

    assert verify_password("secreta123", stored)
    assert not verify_password("otra", stored)
    assert not verify_password("secreta123", "corrupto")


def test_login_and_me(client):
    response = login(client)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == settings.jwt_expire_minutes * 60

    me = client.get("/api/v1/auth/me", headers=auth_header(body["access_token"]))
    assert me.json() == {"username": "ana", "role": "user"}


@pytest.mark.parametrize(
    ("username", "password"), [("ana", "incorrecta"), ("nadie", "secreta123")]
)
def test_login_rejects_bad_credentials(client, username, password):
    response = login(client, username, password)

    assert response.status_code == 401
    assert response.json()["detail"] == "Usuario o contraseña incorrectos"


@pytest.mark.parametrize(
    ("method", "path"),
    [("get", "/metrics"), ("post", "/predict"), ("post", "/predict/csv")],
)
def test_private_endpoints_require_token(client, method, path):
    response = getattr(client, method)(f"/api/v1{path}")

    assert response.status_code == 401


def test_health_is_public(client):
    assert client.get("/api/v1/health").status_code == 200


def test_predict_with_token(client):
    token = login(client).json()["access_token"]

    response = client.post(
        "/api/v1/predict",
        json={"transactions": [make_transaction()]},
        headers=auth_header(token),
    )

    assert response.status_code == 200


def test_rejects_invalid_token(client):
    response = client.get("/api/v1/auth/me", headers=auth_header("no-es-un-jwt"))

    assert response.status_code == 401


def test_rejects_expired_token(client, monkeypatch):
    monkeypatch.setattr(settings, "jwt_expire_minutes", -1)
    token, _ = create_token("ana")

    response = client.get("/api/v1/auth/me", headers=auth_header(token))

    assert response.status_code == 401


def test_auth_without_database(client_with_model_path, pipeline_path, monkeypatch):
    monkeypatch.setattr(main, "open_repositories", lambda _url: (None, None, None))

    with client_with_model_path(pipeline_path, authenticated=False) as client:
        assert login(client).status_code == 503
        assert client.get("/api/v1/metrics").status_code == 503


def test_rejects_token_of_deleted_user(client):
    token, _ = create_token("borrado")

    response = client.get("/api/v1/auth/me", headers=auth_header(token))

    assert response.status_code == 401

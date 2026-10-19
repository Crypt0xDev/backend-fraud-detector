from conftest import ADMIN, ANALYST, login

from utils.token import create_download_token


def test_login_y_me(client, analyst):
    response = client.get("/api/v1/auth/me", headers=analyst)
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == ANALYST[0]
    assert body["root"] is False
    assert body["permissions"] == {
        "lotes": ["ver", "eliminar"],
        "predicciones": ["ver", "crear"],
        "modelo": ["ver"],
        "visualizacion": ["ver"],
    }


def test_login_falla_con_contrasena_o_usuario_incorrectos(client):
    for username, password in ((ADMIN[0], "incorrecta"), ("nadie", "incorrecta")):
        response = client.post(
            "/api/v1/auth/login", data={"username": username, "password": password}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Usuario o contraseña incorrectos"


def test_me_sin_token_o_con_token_falso(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    headers = {"Authorization": "Bearer no-es-un-jwt"}
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_token_de_descarga_no_sirve_como_sesion(client):
    token = create_download_token("x/input.csv", "x.csv", 60)
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_cambiar_contrasena_cierra_las_sesiones(client, analyst):
    response = client.patch(
        "/api/v1/users/me/change-password",
        json={
            "current_password": ANALYST[1],
            "new_password": "nueva-pass-123",
            "confirm_password": "nueva-pass-123",
        },
        headers=analyst,
    )
    assert response.status_code == 204
    assert client.get("/api/v1/auth/me", headers=analyst).status_code == 401
    login(client, ANALYST[0], "nueva-pass-123")


def test_cambiar_contrasena_exige_la_actual(client, analyst):
    response = client.patch(
        "/api/v1/users/me/change-password",
        json={
            "current_password": "incorrecta",
            "new_password": "nueva-pass-123",
            "confirm_password": "nueva-pass-123",
        },
        headers=analyst,
    )
    assert response.status_code == 400


def test_deshabilitar_y_rehabilitar_no_revive_tokens_viejos(client, admin, analyst):
    url = f"/api/v1/users/{ANALYST[0]}"
    assert client.patch(f"{url}/disable", headers=admin).status_code == 204
    assert client.get("/api/v1/auth/me", headers=analyst).status_code == 401
    response = client.post(
        "/api/v1/auth/login", data={"username": ANALYST[0], "password": ANALYST[1]}
    )
    assert response.status_code == 401

    assert client.patch(f"{url}/enable", headers=admin).status_code == 204
    # El token anterior a deshabilitarlo ya no debe valer
    assert client.get("/api/v1/auth/me", headers=analyst).status_code == 401
    login(client, *ANALYST)


def test_limite_de_intentos_por_usuario(client):
    for _ in range(10):
        client.post("/api/v1/auth/login", data={"username": "admin", "password": "x"})
    response = client.post(
        "/api/v1/auth/login", data={"username": ADMIN[0], "password": ADMIN[1]}
    )
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"


def test_limite_de_intentos_por_ip_aunque_cambie_el_usuario(client):
    statuses = [
        client.post(
            "/api/v1/auth/login", data={"username": f"u{i}", "password": "x"}
        ).status_code
        for i in range(80)
    ]
    assert statuses[0] == 401
    assert 429 in statuses


def test_demasiados_logins_simultaneos_dan_503(client, monkeypatch):
    import threading

    from app.auth.usecases import use_auth_login

    # Todos los cupos ocupados: el login no espera para siempre
    monkeypatch.setattr(use_auth_login, "LOGIN_SLOTS", threading.BoundedSemaphore(1))
    monkeypatch.setattr(use_auth_login, "LOGIN_SLOT_TIMEOUT_SECONDS", 0.05)
    use_auth_login.LOGIN_SLOTS.acquire()
    response = client.post(
        "/api/v1/auth/login", data={"username": ADMIN[0], "password": ADMIN[1]}
    )
    assert response.status_code == 503
    use_auth_login.LOGIN_SLOTS.release()
    login(client, *ADMIN)


def test_tokens_sin_typ_de_versiones_anteriores_siguen_valiendo(client, admin):
    from datetime import UTC, datetime, timedelta

    import jwt

    from utils.token import ALGORITHM, jwt_secret

    old = jwt.encode(
        {"sub": ADMIN[0], "ver": 0, "exp": datetime.now(UTC) + timedelta(minutes=5)},
        jwt_secret(),
        algorithm=ALGORITHM,
    )
    headers = {"Authorization": f"Bearer {old}"}
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200

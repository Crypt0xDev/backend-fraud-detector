import threading

import pytest
from conftest import ADMIN, ANALYST, login

from app.user.usecases.use_user_roles import ensure_not_last_root
from app.user.user_entity import User
from app.user.user_schema import ACTIVE
from config import database
from fastapi import HTTPException
from utils.password import hash_password


def test_solo_el_root_gestiona_usuarios(client, analyst):
    assert client.get("/api/v1/users", headers=analyst).status_code == 403
    response = client.post(
        "/api/v1/users",
        json={"username": "x", "password": "password-123"},
        headers=analyst,
    )
    assert response.status_code == 403


def test_crear_usuario_con_rol_por_defecto(client, admin):
    response = client.post(
        "/api/v1/users",
        json={"username": "nuevo", "password": "password-123"},
        headers=admin,
    )
    assert response.status_code == 201
    assert response.content == b""
    body = client.get("/api/v1/users/nuevo", headers=admin).json()
    assert body["root"] is False
    assert [role["name"] for role in body["roles"]] == ["Analista"]
    assert "password_hash" not in body


def test_crear_usuario_repetido_da_409(client, admin):
    payload = {"username": ANALYST[0], "password": "password-123"}
    response = client.post("/api/v1/users", json=payload, headers=admin)
    assert response.status_code == 409
    # Admin y admin serían el mismo usuario a la vista
    payload["username"] = ANALYST[0].upper()
    response = client.post("/api/v1/users", json=payload, headers=admin)
    assert response.status_code == 409


def test_no_acepta_campos_desconocidos(client, admin):
    response = client.post(
        "/api/v1/users",
        json={"username": "x1", "password": "password-123", "token_version": 9},
        headers=admin,
    )
    assert response.status_code == 422


def test_username_no_valido(client, admin):
    for username in ("..", "a/b", "con espacio"):
        response = client.post(
            "/api/v1/users",
            json={"username": username, "password": "password-123"},
            headers=admin,
        )
        assert response.status_code == 422, username


def test_roles_inexistentes_dan_400(client, admin):
    response = client.post(
        "/api/v1/users",
        json={"username": "x2", "password": "password-123", "role_ids": [999]},
        headers=admin,
    )
    assert response.status_code == 400


def test_el_root_no_se_borra_ni_deshabilita_a_si_mismo(client, admin):
    url = f"/api/v1/users/{ADMIN[0]}"
    assert client.delete(url, headers=admin).status_code == 409
    assert client.patch(f"{url}/disable", headers=admin).status_code == 409
    response = client.patch(url, json={"root": False}, headers=admin)
    assert response.status_code == 409


def test_debe_quedar_un_root(client, admin):
    client.post(
        "/api/v1/users",
        json={"username": "root2", "password": "password-123", "root": True},
        headers=admin,
    )
    root2 = login(client, "root2", "password-123")
    # root2 deshabilita al admin; ahora root2 es el último
    assert (
        client.patch(f"/api/v1/users/{ADMIN[0]}/disable", headers=root2).status_code
        == 204
    )
    response = client.patch("/api/v1/users/root2", json={"root": False}, headers=root2)
    assert response.status_code == 409


def test_actualizar_usuario(client, admin, analyst):
    response = client.patch(
        f"/api/v1/users/{ANALYST[0]}", json={"password": "otra-pass-123"}, headers=admin
    )
    assert response.status_code == 200
    # Cambiar la contraseña cierra sus sesiones
    assert client.get("/api/v1/auth/me", headers=analyst).status_code == 401
    response = client.patch(f"/api/v1/users/{ANALYST[0]}", json={}, headers=admin)
    assert response.status_code == 422
    response = client.patch("/api/v1/users/nadie", json={"root": True}, headers=admin)
    assert response.status_code == 404


def test_listar_y_ver_usuarios(client, admin):
    response = client.get("/api/v1/users", headers=admin)
    assert response.status_code == 200
    body = response.json()
    assert {u["username"] for u in body["items"]} == {ADMIN[0], ANALYST[0]}
    assert body["total"] == 2
    second = client.get("/api/v1/users?page=2&page_size=1", headers=admin).json()
    assert len(second["items"]) == 1 and second["total"] == 2
    assert client.get("/api/v1/users/nadie", headers=admin).status_code == 404


def test_borrar_usuario_es_logico_y_guarda_sus_lotes(client, admin, analyst, tmp_path):
    from conftest import CSV_HEADER, CSV_ROW

    csv = f"{CSV_HEADER}\n{CSV_ROW}\n".encode()
    response = client.post(
        "/api/v1/predict/batch",
        files={"file": ("lote.csv", csv, "text/csv")},
        headers=analyst,
    )
    batch_id = response.json()["batch_id"]
    assert batch_id
    batch_dir = tmp_path / "batches" / batch_id
    assert batch_dir.is_dir()

    assert (
        client.delete(f"/api/v1/users/{ANALYST[0]}", headers=admin).status_code == 204
    )
    # Sus lotes y archivos se quedan guardados
    assert batch_dir.is_dir()
    listed = client.get("/api/v1/batches?all=true", headers=admin).json()
    assert listed["total"] == 1

    # Ya no entra, no aparece y su nombre no se puede volver a usar
    assert client.get("/api/v1/auth/me", headers=analyst).status_code == 401
    response = client.post("/api/v1/auth/login", data={"username": ANALYST[0], "password": ANALYST[1]})
    assert response.status_code == 401
    assert client.get(f"/api/v1/users/{ANALYST[0]}", headers=admin).status_code == 404
    usernames = {u["username"] for u in client.get("/api/v1/users", headers=admin).json()["items"]}
    assert ANALYST[0] not in usernames
    assert client.delete(f"/api/v1/users/{ANALYST[0]}", headers=admin).status_code == 404
    assert client.patch(f"/api/v1/users/{ANALYST[0]}/enable", headers=admin).status_code == 404
    payload = {"username": ANALYST[0], "password": "password-123"}
    assert client.post("/api/v1/users", json=payload, headers=admin).status_code == 409


def test_ultimo_root_con_peticiones_simultaneas(client, is_postgres):
    """Dos roots que se deshabilitan entre sí a la vez no dejan el sistema sin root"""
    if not is_postgres:
        pytest.skip("SQLite no soporta SELECT ... FOR UPDATE")
    with database.SessionLocal() as db:
        db.add(
            User(
                username="root2",
                password_hash=hash_password("password-123"),
                root=True,
                state=ACTIVE,
            )
        )
        db.commit()

    first = database.SessionLocal()
    second = database.SessionLocal()
    errors: list[int] = []
    try:
        target = first.get(User, "root2")
        assert target is not None
        ensure_not_last_root(first, target)  # bloquea las filas de los roots

        def disable_admin():
            other = second.get(User, ADMIN[0])
            assert other is not None
            try:
                ensure_not_last_root(second, other)
                other.state = "Deshabilitado"
                second.commit()
            except HTTPException:
                second.rollback()
                errors.append(409)

        thread = threading.Thread(target=disable_admin)
        thread.start()
        thread.join(timeout=0.5)
        assert thread.is_alive(), "la segunda transacción debía esperar el bloqueo"

        target.state = "Deshabilitado"
        first.commit()
        thread.join(timeout=5)
    finally:
        first.close()
        second.close()

    assert errors == [409]

from conftest import ANALYST, TRANSACTION


def module_permission_ids(client, admin, wanted: dict[str, set[str]]) -> list[int]:
    tree = client.get("/api/v1/roles/modules-with-permissions", headers=admin).json()
    return [
        permission["id"]
        for module in tree
        for permission in module["permissions"]
        if permission["name"] in wanted.get(module["code"], set())
    ]


def test_solo_el_root_gestiona_roles(client, analyst):
    assert client.get("/api/v1/roles", headers=analyst).status_code == 403


def test_crear_listar_actualizar_y_borrar_rol(client, admin):
    ids = module_permission_ids(client, admin, {"lotes": {"ver"}})
    response = client.post(
        "/api/v1/roles",
        json={
            "name": "Lector",
            "description": "Solo ve lotes",
            "module_permission_ids": ids,
        },
        headers=admin,
    )
    assert response.status_code == 201
    role = response.json()
    assert role["permissions"] == {"lotes": ["ver"]}

    roles = client.get("/api/v1/roles", headers=admin).json()
    assert {r["name"] for r in roles} == {"Analista", "Lector"}

    more = module_permission_ids(client, admin, {"lotes": {"ver"}, "modelo": {"ver"}})
    response = client.put(
        f"/api/v1/roles/{role['id']}",
        json={
            "name": "Lector",
            "description": "Lotes y modelo",
            "module_permission_ids": more,
        },
        headers=admin,
    )
    assert response.status_code == 200
    assert response.json()["permissions"] == {"lotes": ["ver"], "modelo": ["ver"]}

    assert (
        client.delete(f"/api/v1/roles/{role['id']}", headers=admin).status_code == 204
    )
    assert client.get(f"/api/v1/roles/{role['id']}", headers=admin).status_code == 404


def test_nombre_de_rol_repetido_da_409(client, admin):
    payload = {"name": "Analista", "description": "otra vez"}
    assert client.post("/api/v1/roles", json=payload, headers=admin).status_code == 409
    other = client.post(
        "/api/v1/roles", json={"name": "Otro", "description": "x" * 3}, headers=admin
    ).json()
    response = client.put(f"/api/v1/roles/{other['id']}", json=payload, headers=admin)
    assert response.status_code == 409


def test_permisos_inexistentes_dan_400(client, admin):
    response = client.post(
        "/api/v1/roles",
        json={"name": "Malo", "description": "abc", "module_permission_ids": [9999]},
        headers=admin,
    )
    assert response.status_code == 400


def test_no_se_borra_un_rol_asignado(client, admin):
    analyst_role = next(
        r
        for r in client.get("/api/v1/roles", headers=admin).json()
        if r["name"] == "Analista"
    )
    response = client.delete(f"/api/v1/roles/{analyst_role['id']}", headers=admin)
    assert response.status_code == 409


def test_los_permisos_del_rol_se_aplican_en_cada_peticion(client, admin, analyst):
    ids = module_permission_ids(client, admin, {"lotes": {"ver"}})
    role = client.post(
        "/api/v1/roles",
        json={
            "name": "Lector",
            "description": "Solo ve lotes",
            "module_permission_ids": ids,
        },
        headers=admin,
    ).json()
    response = client.patch(
        f"/api/v1/users/{ANALYST[0]}", json={"role_ids": [role["id"]]}, headers=admin
    )
    assert response.status_code == 200

    # El mismo token, sin volver a iniciar sesión, ya no puede predecir
    response = client.post(
        "/api/v1/predict", json={"transactions": [TRANSACTION]}, headers=analyst
    )
    assert response.status_code == 403
    assert client.get("/api/v1/batches", headers=analyst).status_code == 200
    me = client.get("/api/v1/auth/me", headers=analyst).json()
    assert me["permissions"] == {"lotes": ["ver"]}


def count_queries(engine, action) -> int:
    from sqlalchemy import event

    statements = []

    def record(*_args):
        statements.append(1)

    event.listen(engine, "before_cursor_execute", record)
    try:
        action()
    finally:
        event.remove(engine, "before_cursor_execute", record)
    return len(statements)


def test_listar_roles_y_usuarios_no_hace_una_consulta_por_fila(client, admin, engine):
    ids = module_permission_ids(client, admin, {"lotes": {"ver", "eliminar"}})

    def list_all():
        assert client.get("/api/v1/roles", headers=admin).status_code == 200
        assert client.get("/api/v1/users", headers=admin).status_code == 200

    before = count_queries(engine, list_all)
    for i in range(5):
        role = client.post(
            "/api/v1/roles",
            json={
                "name": f"Rol {i}",
                "description": "abc",
                "module_permission_ids": ids,
            },
            headers=admin,
        ).json()
        client.post(
            "/api/v1/users",
            json={
                "username": f"u{i}",
                "password": "password-123",
                "role_ids": [role["id"]],
            },
            headers=admin,
        )
    assert count_queries(engine, list_all) == before

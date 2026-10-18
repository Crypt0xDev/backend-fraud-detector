import pandas as pd
import pytest

from tests.factories import make_transaction
from utils.auth import get_current_user
from utils.password import hash_password, verify_password


@pytest.fixture
def client(client_with_model_path, pipeline_path):
    with client_with_model_path(pipeline_path) as client:
        users = client.app.state.users
        users.save("jefe", hash_password("admin1234"), "admin")
        users.save("ana", hash_password("ana12345"))
        users.save("beto", hash_password("beto1234"))
        yield client


def act_as(client, username):
    client.app.dependency_overrides[get_current_user] = lambda: username


def upload(client):
    content = pd.DataFrame([make_transaction(isFraud=1), make_transaction()])
    return client.post(
        "/api/v1/predict/csv",
        files={"file": ("pagos.csv", content.to_csv(index=False).encode(), "text/csv")},
    ).json()["batch_id"]


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/users"),
        ("post", "/users"),
        ("patch", "/users/beto"),
        ("delete", "/users/beto"),
    ],
)
def test_normal_user_cannot_manage_users(client, method, path):
    act_as(client, "ana")

    response = getattr(client, method)(f"/api/v1{path}")

    assert response.status_code == 403


def test_admin_lists_users(client):
    act_as(client, "jefe")

    users = client.get("/api/v1/users").json()

    assert {(u["username"], u["role"]) for u in users} == {
        ("jefe", "admin"),
        ("ana", "user"),
        ("beto", "user"),
    }


def test_admin_creates_user(client):
    act_as(client, "jefe")

    response = client.post(
        "/api/v1/users", json={"username": "carla", "password": "carla1234"}
    )

    assert response.status_code == 201
    assert response.json()["role"] == "user"
    users = client.app.state.users
    assert verify_password("carla1234", users.get_password_hash("carla"))


@pytest.mark.parametrize(
    ("payload", "status"),
    [
        ({"username": "ana", "password": "otra12345"}, 409),
        ({"username": "carla", "password": "corta"}, 422),
        ({"username": "carla", "password": "carla1234", "role": "dios"}, 422),
    ],
)
def test_admin_create_rejects_invalid(client, payload, status):
    act_as(client, "jefe")

    assert client.post("/api/v1/users", json=payload).status_code == status


def test_existing_user_is_not_overwritten_on_create(client):
    act_as(client, "jefe")

    client.post("/api/v1/users", json={"username": "ana", "password": "otra12345"})

    users = client.app.state.users
    assert verify_password("ana12345", users.get_password_hash("ana"))


def test_admin_changes_role_and_password(client):
    act_as(client, "jefe")

    response = client.patch(
        "/api/v1/users/ana", json={"role": "admin", "password": "nueva1234"}
    )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    users = client.app.state.users
    assert verify_password("nueva1234", users.get_password_hash("ana"))


def test_admin_cannot_demote_self(client):
    act_as(client, "jefe")

    response = client.patch("/api/v1/users/jefe", json={"role": "user"})

    assert response.status_code == 409
    assert client.app.state.users.get_role("jefe") == "admin"


def test_update_requires_changes(client):
    act_as(client, "jefe")

    assert client.patch("/api/v1/users/ana", json={}).status_code == 422


def test_update_unknown_user(client):
    act_as(client, "jefe")

    assert (
        client.patch("/api/v1/users/nadie", json={"role": "admin"}).status_code == 404
    )


def test_admin_cannot_delete_self(client):
    act_as(client, "jefe")

    assert client.delete("/api/v1/users/jefe").status_code == 409


def test_delete_user_removes_their_files(client):
    act_as(client, "ana")
    batch_id = upload(client)
    act_as(client, "jefe")

    assert client.delete("/api/v1/users/ana").status_code == 204
    assert not client.app.state.users.exists("ana")
    assert not any(
        path.startswith(batch_id) for path in client.app.state.storage.objects
    )


def test_users_only_see_own_batches(client):
    act_as(client, "ana")
    batch_id = upload(client)
    act_as(client, "beto")

    assert client.get("/api/v1/batches").json()["items"] == []
    assert client.get(f"/api/v1/batches/{batch_id}/files/input").status_code == 404
    assert client.delete(f"/api/v1/batches/{batch_id}").status_code == 404


def test_normal_user_cannot_list_all_batches(client):
    act_as(client, "ana")

    assert client.get("/api/v1/batches", params={"all": True}).status_code == 403


def test_admin_moderates_all_batches(client):
    act_as(client, "ana")
    batch_id = upload(client)
    act_as(client, "jefe")

    assert client.get("/api/v1/batches").json()["items"] == []
    everyone = client.get("/api/v1/batches", params={"all": True}).json()["items"]
    assert [(b["id"], b["username"]) for b in everyone] == [(batch_id, "ana")]
    assert client.get(f"/api/v1/batches/{batch_id}/files/input").status_code == 200
    assert client.delete(f"/api/v1/batches/{batch_id}").status_code == 204
    assert client.get("/api/v1/batches", params={"all": True}).json()["items"] == []


def test_me_reports_admin_role(client):
    act_as(client, "jefe")

    assert client.get("/api/v1/auth/me").json() == {"username": "jefe", "role": "admin"}

import pytest

from tests.factories import make_transaction
from utils.auth import get_current_user
from utils.password import hash_password


@pytest.fixture
def client(client_with_model_path, pipeline_path):
    with client_with_model_path(pipeline_path) as client:
        users = client.app.state.users
        users.save("jefe", hash_password("admin1234"), "admin")
        users.save("ana", hash_password("ana12345"))
        yield client


def act_as(client, username):
    client.app.dependency_overrides[get_current_user] = lambda: username


def predict(client, **overrides):
    return client.post(
        "/api/v1/predict", json={"transactions": [make_transaction(**overrides)]}
    )


def test_prediction_is_saved(client):
    act_as(client, "ana")
    predict(client, nameOrig="C999")

    history = client.get("/api/v1/predictions").json()

    assert history["total"] == 1
    [item] = history["items"]
    assert (item["username"], item["name_orig"], item["type"]) == (
        "ana",
        "C999",
        "TRANSFER",
    )


def test_history_is_per_user(client):
    act_as(client, "ana")
    predict(client)
    act_as(client, "jefe")
    predict(client)
    predict(client)

    assert client.get("/api/v1/predictions").json()["total"] == 2
    assert client.get("/api/v1/predictions?all=true").json()["total"] == 3


def test_normal_user_cannot_see_everyone(client):
    act_as(client, "ana")

    assert client.get("/api/v1/predictions?all=true").status_code == 403


def test_history_limit(client):
    act_as(client, "ana")
    for _ in range(3):
        predict(client)

    history = client.get("/api/v1/predictions?limit=2").json()

    assert (history["total"], len(history["items"])) == (3, 2)


def test_prediction_survives_history_failure(client):
    act_as(client, "ana")
    client.app.state.predictions.fail = True

    assert predict(client).status_code == 200


def test_history_offset(client):
    act_as(client, "ana")
    for _ in range(3):
        predict(client)

    history = client.get("/api/v1/predictions?limit=2&offset=2").json()

    assert (history["total"], len(history["items"])) == (3, 1)


def test_history_alerts_only(client):
    act_as(client, "ana")
    client.app.state.predictions.rows.clear()
    predict(client)

    history = client.get("/api/v1/predictions?alerts_only=true").json()

    assert history["total"] == 1
    assert all(item["is_fraud"] for item in history["items"])

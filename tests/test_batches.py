import io
import uuid

import pandas as pd
import pytest

import main
from tests.factories import make_transaction
from utils.auth import get_current_user


@pytest.fixture
def client(client_with_model_path, pipeline_path):
    with client_with_model_path(pipeline_path) as client:
        yield client


def upload(client, name="pagos.csv"):
    content = pd.DataFrame([make_transaction(isFraud=1), make_transaction()])
    return client.post(
        "/api/v1/predict/csv",
        files={"file": (name, content.to_csv(index=False).encode(), "text/csv")},
    )


def test_csv_prediction_is_saved(client):
    response = upload(client)

    batch_id = response.json()["batch_id"]
    storage = client.app.state.storage
    assert set(storage.objects) == {
        f"{batch_id}/input.csv",
        f"{batch_id}/predictions.csv",
    }

    saved = pd.read_csv(io.BytesIO(storage.objects[f"{batch_id}/predictions.csv"]))
    assert {"isFraud", "fraud_probability", "is_fraud"} <= set(saved.columns)
    assert len(saved) == 2


def test_list_batches(client):
    batch_id = upload(client).json()["batch_id"]

    batches = client.get("/api/v1/batches").json()

    assert [b["id"] for b in batches] == [batch_id]
    assert batches[0]["file_name"] == "pagos.csv"
    assert batches[0]["total_rows"] == 2


def test_batch_file_url(client):
    batch_id = upload(client).json()["batch_id"]

    response = client.get(f"/api/v1/batches/{batch_id}/files/predictions")

    assert response.status_code == 200
    assert response.json()["url"].endswith("download=pagos_predicciones.csv")


def test_batch_file_rejects_unknown_kind(client):
    batch_id = upload(client).json()["batch_id"]

    response = client.get(f"/api/v1/batches/{batch_id}/files/otro")

    assert response.status_code == 422


def test_batches_are_private(client):
    batch_id = upload(client).json()["batch_id"]
    client.app.dependency_overrides[get_current_user] = lambda: "otro"

    assert client.get("/api/v1/batches").json() == []
    assert client.get(f"/api/v1/batches/{batch_id}/files/input").status_code == 404
    assert client.delete(f"/api/v1/batches/{batch_id}").status_code == 404


def test_delete_batch(client):
    batch_id = upload(client).json()["batch_id"]

    assert client.delete(f"/api/v1/batches/{batch_id}").status_code == 204
    assert client.get("/api/v1/batches").json() == []
    assert client.app.state.storage.objects == {}


def test_delete_unknown_batch(client):
    response = client.delete(f"/api/v1/batches/{uuid.uuid4()}")

    assert response.status_code == 404


def test_prediction_survives_storage_failure(client):
    client.app.state.storage.fail = True

    response = upload(client)

    assert response.status_code == 200
    assert response.json()["batch_id"] is None
    assert client.get("/api/v1/batches").json() == []


def test_history_without_storage(client_with_model_path, pipeline_path, monkeypatch):
    monkeypatch.setattr(main, "open_storage", lambda *_args: None)

    with client_with_model_path(pipeline_path) as client:
        assert upload(client).json()["batch_id"] is None
        file_url = client.get(f"/api/v1/batches/{uuid.uuid4()}/files/input")
        assert file_url.status_code == 503


def test_json_prediction_is_not_saved(client):
    response = client.post(
        "/api/v1/predict", json={"transactions": [make_transaction()]}
    )

    assert response.json()["batch_id"] is None

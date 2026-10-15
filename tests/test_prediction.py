import pandas as pd

from app.shared.config import settings
from tests.factories import make_transaction


def test_predict_without_model(client_with_model_path, tmp_path):
    with client_with_model_path(tmp_path / "missing.joblib") as client:
        response = client.post(
            "/api/v1/predict", json={"transactions": [make_transaction()]}
        )

    assert response.status_code == 503


def test_predict_batch(client_with_model_path, pipeline_path):
    transactions = [make_transaction(), make_transaction(type="PAYMENT", amount=10.0)]

    with client_with_model_path(pipeline_path) as client:
        response = client.post("/api/v1/predict", json={"transactions": transactions})

    assert response.status_code == 200
    body = response.json()
    assert body["threshold"] == 0.5
    assert len(body["predictions"]) == 2
    for prediction in body["predictions"]:
        assert 0 <= prediction["fraud_probability"] <= 1
        assert prediction["is_fraud"] == (prediction["fraud_probability"] >= 0.5)


def test_predict_without_optional_names(client_with_model_path, pipeline_path):
    transaction = make_transaction()
    del transaction["nameOrig"], transaction["nameDest"]

    with client_with_model_path(pipeline_path) as client:
        response = client.post("/api/v1/predict", json={"transactions": [transaction]})

    assert response.status_code == 200


def test_predict_rejects_empty_batch(client_with_model_path, pipeline_path):
    with client_with_model_path(pipeline_path) as client:
        response = client.post("/api/v1/predict", json={"transactions": []})

    assert response.status_code == 422


def test_predict_rejects_invalid_transaction(client_with_model_path, pipeline_path):
    transactions = [make_transaction(type="CRYPTO"), make_transaction(amount=-5)]

    with client_with_model_path(pipeline_path) as client:
        response = client.post("/api/v1/predict", json={"transactions": transactions})

    assert response.status_code == 422


def to_csv(transactions):
    return pd.DataFrame(transactions).to_csv(index=False).encode()


def post_csv(client, content):
    return client.post(
        "/api/v1/predict/csv", files={"file": ("data.csv", content, "text/csv")}
    )


def test_predict_csv_with_raw_paysim_columns(client_with_model_path, pipeline_path):
    transactions = [
        make_transaction(isFraud=1, isFlaggedFraud=0),
        make_transaction(type="PAYMENT", nameDest=None, isFraud=0, isFlaggedFraud=0),
    ]

    with client_with_model_path(pipeline_path) as client:
        response = post_csv(client, to_csv(transactions))

    assert response.status_code == 200
    assert len(response.json()["predictions"]) == 2


def test_predict_csv_without_model(client_with_model_path, tmp_path):
    with client_with_model_path(tmp_path / "missing.joblib") as client:
        response = post_csv(client, to_csv([make_transaction()]))

    assert response.status_code == 503


def test_predict_csv_rejects_invalid_rows(client_with_model_path, pipeline_path):
    transactions = [make_transaction(), make_transaction(type="CRYPTO")]

    with client_with_model_path(pipeline_path) as client:
        response = post_csv(client, to_csv(transactions))

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][:2] == [1, "type"]


def test_predict_csv_rejects_missing_columns(client_with_model_path, pipeline_path):
    transaction = make_transaction()
    del transaction["amount"]

    with client_with_model_path(pipeline_path) as client:
        response = post_csv(client, to_csv([transaction]))

    assert response.status_code == 422


def test_predict_csv_rejects_empty_file(client_with_model_path, pipeline_path):
    with client_with_model_path(pipeline_path) as client:
        empty = post_csv(client, b"")
        header_only = post_csv(client, b"step,type,amount\n")

    assert empty.status_code == 422
    assert header_only.status_code == 422


def test_predict_csv_rejects_too_many_rows(
    client_with_model_path, pipeline_path, monkeypatch
):
    monkeypatch.setattr(settings, "max_batch_rows", 2)

    with client_with_model_path(pipeline_path) as client:
        response = post_csv(client, to_csv([make_transaction()] * 3))

    assert response.status_code == 422

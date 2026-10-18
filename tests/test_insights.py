import io

import pandas as pd
import pytest

from tests.factories import make_transaction


@pytest.fixture
def client(client_with_model_path, pipeline_path):
    with client_with_model_path(pipeline_path) as client:
        yield client


def sample_frame(n=10):
    return pd.DataFrame(
        {
            "step": range(1, n + 1),
            "type": ["TRANSFER", "PAYMENT"] * (n // 2),
            "amount": [100.0] * n,
            "oldbalanceOrg": [100.0] * n,
            "oldbalanceDest": [0.0] * n,
            "isFraud": [1, 0] * (n // 2),
            "alert": [1, 0] * (n // 2),
            "score": [i / n for i in range(n)],
            "pc1": [0.0] * n,
            "pc2": [0.0] * n,
            "pc3": [0.0] * n,
        }
    )


def test_model_info(client):
    info = client.get("/api/v1/model/info").json()

    assert info["loaded"] is True
    assert info["threshold"] == 0.5
    assert info["risk_levels"]["source"] == "FRAUD_THRESHOLD"
    assert info["limits"]["max_batch_rows"] > 0


def test_experiments_unavailable_without_artifacts(client):
    assert client.get("/api/v1/experiments").status_code == 503


def test_experiments(client):
    client.app.state.experiments = {
        "recommended": "v002",
        "experiments": [
            {
                "version": "v002",
                "model_name": "XGBoost (pre)",
                "model_type": "xgboost",
                "feature_set": "pre",
                "val_pr_auc": 0.5,
                "pr_auc": 0.4,
                "recall": 0.3,
            }
        ],
    }

    body = client.get("/api/v1/experiments").json()
    assert body["recommended"] == "v002"
    assert client.get("/api/v1/experiments/v002").json()["recall"] == 0.3
    assert client.get("/api/v1/experiments/v999").status_code == 404


def test_dataset_profile(client):
    assert client.get("/api/v1/dataset/profile").status_code == 503
    client.app.state.profile = {"rows": 10, "classes": {"fraud": 1}}

    assert client.get("/api/v1/dataset/profile").json()["classes"] == {"fraud": 1}


def test_visualization_sample_filters(client):
    client.app.state.sample = sample_frame()

    body = client.get(
        "/api/v1/visualization/sample?types=TRANSFER&score_min=0.2&limit=2"
    ).json()

    assert body["total_in_sample"] == 10
    assert body["matched"] == 4
    assert body["returned"] == 2
    point = body["points"][0]
    assert point["type"] == "TRANSFER" and point["score"] >= 0.2
    assert {"label", "alert", "score", "pc1"} <= set(point)


def test_visualization_rejects_unknown_type(client):
    client.app.state.sample = sample_frame()

    assert client.get("/api/v1/visualization/sample?types=HACK").status_code == 422


def test_predict_batch_alias_escapes_formulas(client):
    content = pd.DataFrame([make_transaction(nameOrig="=CMD()")]).to_csv(index=False)

    response = client.post(
        "/api/v1/predict/batch",
        files={"file": ("x.csv", content.encode(), "text/csv")},
    )

    assert response.status_code == 200
    batch_id = response.json()["batch_id"]
    saved = client.app.state.storage.objects[f"{batch_id}/predictions.csv"]
    frame = pd.read_csv(io.BytesIO(saved))
    assert frame.loc[0, "nameOrig"] == "'=CMD()"
    assert "risk_level" in frame.columns

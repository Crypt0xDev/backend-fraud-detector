import json


def test_metrics_without_file(client_with_model_path, tmp_path):
    with client_with_model_path(tmp_path / "missing.joblib") as client:
        response = client.get("/api/v1/metrics")

    assert response.status_code == 503


def test_metrics(client_with_model_path, tmp_path):
    metrics = {"roc_auc": 0.99, "recall": 0.91, "threshold": 0.5}
    path = tmp_path / "metrics.json"
    path.write_text(json.dumps(metrics))

    with client_with_model_path(tmp_path / "missing.joblib", path) as client:
        response = client.get("/api/v1/metrics")

    assert response.status_code == 200
    assert response.json() == metrics


def test_metrics_with_invalid_json(client_with_model_path, tmp_path):
    path = tmp_path / "metrics.json"
    path.write_text("no es json")

    with client_with_model_path(tmp_path / "missing.joblib", path) as client:
        response = client.get("/api/v1/metrics")

    assert response.status_code == 503


def test_metrics_that_are_not_an_object(client_with_model_path, tmp_path):
    path = tmp_path / "metrics.json"
    path.write_text("[0.99, 0.91]")

    with client_with_model_path(tmp_path / "missing.joblib", path) as client:
        response = client.get("/api/v1/metrics")

    assert response.status_code == 503

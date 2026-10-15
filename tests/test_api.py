import joblib

from app.shared.model_loader import file_sha256
from tests.factories import save_pipeline


def get_health(client_with_model_path, path, **kwargs):
    with client_with_model_path(path, **kwargs) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    return response.json()


def test_health_without_artifacts(client_with_model_path, tmp_path):
    assert get_health(client_with_model_path, tmp_path / "missing.joblib") == {
        "status": "ok",
        "model_loaded": False,
        "metrics_loaded": False,
    }


def test_health_with_artifacts(client_with_model_path, pipeline_path):
    (pipeline_path.parent / "metrics.json").write_text("{}")

    assert get_health(client_with_model_path, pipeline_path) == {
        "status": "ok",
        "model_loaded": True,
        "metrics_loaded": True,
    }


def test_health_with_corrupt_model(client_with_model_path, tmp_path):
    path = tmp_path / "pipeline.joblib"
    path.write_text("no es un joblib")

    assert not get_health(client_with_model_path, path)["model_loaded"]


def test_health_with_object_that_cannot_predict(client_with_model_path, tmp_path):
    path = tmp_path / "pipeline.joblib"
    joblib.dump({"dummy": True}, path)

    assert not get_health(client_with_model_path, path)["model_loaded"]


def test_model_with_unknown_columns_is_rejected(client_with_model_path, tmp_path):
    path = save_pipeline(tmp_path / "pipeline.joblib", extra_columns=["balanceDiff"])

    assert not get_health(client_with_model_path, path)["model_loaded"]


def test_model_with_matching_sha256(client_with_model_path, pipeline_path):
    sha256 = file_sha256(pipeline_path).upper()

    assert get_health(client_with_model_path, pipeline_path, sha256=sha256)[
        "model_loaded"
    ]


def test_model_with_wrong_sha256(client_with_model_path, pipeline_path):
    assert not get_health(client_with_model_path, pipeline_path, sha256="0" * 64)[
        "model_loaded"
    ]

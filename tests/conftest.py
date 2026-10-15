import pytest
from fastapi.testclient import TestClient

from app.shared.config import settings
from main import app
from tests.factories import save_pipeline


@pytest.fixture
def client_with_model_path(monkeypatch):
    def make(path, metrics_path=None, sha256=None):
        monkeypatch.setattr(settings, "model_path", path)
        monkeypatch.setattr(
            settings, "metrics_path", metrics_path or path.parent / "metrics.json"
        )
        monkeypatch.setattr(settings, "model_sha256", sha256)
        return TestClient(app)

    return make


@pytest.fixture
def pipeline_path(tmp_path):
    return save_pipeline(tmp_path / "pipeline.joblib")

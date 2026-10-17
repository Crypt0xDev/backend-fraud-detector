import pytest
from fastapi.testclient import TestClient

import main
from config.settings import settings
from main import app
from tests.factories import (
    InMemoryBatchRepository,
    InMemoryStorage,
    InMemoryUserRepository,
    save_pipeline,
)
from utils.auth import get_current_user


@pytest.fixture(autouse=True)
def in_memory_services(monkeypatch):
    monkeypatch.setattr(
        main,
        "open_repositories",
        lambda _url: (None, InMemoryUserRepository(), InMemoryBatchRepository()),
    )
    monkeypatch.setattr(main, "open_storage", lambda *_args: InMemoryStorage())


@pytest.fixture
def client_with_model_path(monkeypatch):
    def make(path, metrics_path=None, sha256=None, authenticated=True):
        monkeypatch.setattr(settings, "model_path", path)
        monkeypatch.setattr(
            settings, "metrics_path", metrics_path or path.parent / "metrics.json"
        )
        monkeypatch.setattr(settings, "model_sha256", sha256)
        if authenticated:
            app.dependency_overrides[get_current_user] = lambda: "tester"
        return TestClient(app)

    yield make
    app.dependency_overrides.clear()


@pytest.fixture
def pipeline_path(tmp_path):
    return save_pipeline(tmp_path / "pipeline.joblib")

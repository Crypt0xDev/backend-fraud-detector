from pathlib import Path

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
from tests.prediction_factories import InMemoryPredictionRepository
from utils.auth import get_current_user


@pytest.fixture(autouse=True)
def in_memory_services(monkeypatch):
    monkeypatch.setattr(
        main,
        "open_repositories",
        lambda _url: (None, InMemoryUserRepository(), InMemoryBatchRepository()),
    )
    monkeypatch.setattr(
        main, "open_storage", lambda *_args, **_kwargs: InMemoryStorage()
    )
    monkeypatch.setattr(
        main, "open_prediction_repository", lambda _pool: InMemoryPredictionRepository()
    )
    # Los tests no dependen del .env local
    monkeypatch.setattr(settings, "fraud_threshold", 0.5)
    for name in ("admin_username", "admin_password", "user_username", "user_password"):
        monkeypatch.setattr(settings, name, None)
    for name in ("sample_path", "experiments_path", "profile_path"):
        monkeypatch.setattr(settings, name, Path("no-existe") / name)
    monkeypatch.setattr(settings, "rate_limit_per_minute", 0)


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

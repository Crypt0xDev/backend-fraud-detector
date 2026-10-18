from pathlib import Path
from types import SimpleNamespace

from app.model.model_schema import MetricsOut
from config.settings import Settings
from config.startup_summary import build_summary
from utils.storage import LocalStorage, SupabaseStorage


def make_settings(**overrides):
    values = {
        "database_url": "postgresql://postgres@127.0.0.1:5432/db_faraude",
        "fraud_threshold": 0.9895,
        "api_public_url": "http://localhost:8000",
    }
    return Settings(_env_file=None, **(values | overrides))


def make_state(**overrides):
    values = {
        "users": object(),
        "storage": LocalStorage(Path("storage/batches"), "http://x/download"),
        "model": object(),
        "metrics": MetricsOut(
            version="v001",
            model_name="XGBoost (PaySim)",
            threshold=0.9895,
            pr_auc=0.9982,
        ),
    }
    return SimpleNamespace(**(values | overrides))


def test_summary_with_everything_configured():
    summary = build_summary(make_state(), make_settings())

    assert "PostgreSQL local · db_faraude en 127.0.0.1:5432" in summary
    assert "local · " in summary
    assert "v001 · XGBoost (PaySim) · umbral 0.9895 · PR-AUC 0.9982" in summary
    assert "http://localhost:8000/api/v1" in summary
    assert "http://localhost:8000/docs" in summary


def test_summary_hides_database_password():
    settings = make_settings(
        database_url="postgresql://user:secreto@db.abc.supabase.co:6543/postgres"
    )

    summary = build_summary(make_state(), settings)

    assert "Supabase · postgres en db.abc.supabase.co:6543" in summary
    assert "secreto" not in summary


def test_summary_without_services():
    state = make_state(users=None, storage=None, model=None, metrics=None)

    summary = build_summary(state, make_settings(database_url=None))

    assert "no configurada" in summary
    assert "desactivado" in summary
    assert "no cargado" in summary


def test_summary_supabase_storage():
    state = make_state(storage=SupabaseStorage("https://x.supabase.co", "k", "batches"))

    assert "Supabase · bucket batches" in build_summary(state, make_settings())


def test_summary_warns_about_threshold_mismatch():
    summary = build_summary(make_state(), make_settings(fraud_threshold=0.5))

    assert "umbral 0.5 (el modelo se entrenó con 0.9895)" in summary

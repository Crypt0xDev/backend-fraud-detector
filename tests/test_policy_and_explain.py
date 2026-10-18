import pandas as pd
import pytest

from app.model.model_schema import MetricsOut
from app.prediction.prediction_policy import build_policy
from app.prediction.usecases.use_prediction_csv import escape_formula, safe_csv
from tests.factories import make_transaction
from utils.rate_limit import RateLimiter


def test_policy_reads_risk_levels_from_metrics():
    metrics = MetricsOut(threshold=0.9, risk_levels={"medium": 0.4, "high": 0.9})

    policy = build_policy(metrics, None)

    assert (policy.medium, policy.high, policy.source) == (0.4, 0.9, "metrics.json")
    assert [policy.level(s) for s in (0.1, 0.5, 0.95)] == ["low", "medium", "high"]


def test_policy_override_wins_and_keeps_order():
    metrics = MetricsOut(threshold=0.9, risk_levels={"medium": 0.6, "high": 0.9})

    policy = build_policy(metrics, 0.3)

    assert (policy.medium, policy.high, policy.source) == (0.3, 0.3, "FRAUD_THRESHOLD")


def test_policy_without_metrics():
    assert build_policy(None, None).high == 0.5


@pytest.mark.parametrize("value", ["=1+1", "+cmd", "-2", "@SUM(A1)", "\tx", "\rx"])
def test_escape_formula(value):
    assert escape_formula(value) == "'" + value


def test_safe_csv_only_touches_text():
    csv = safe_csv(pd.DataFrame({"nameOrig": ["=HYPERLINK()"], "amount": [-5.0]}))

    assert csv.decode().splitlines()[1] == "'=HYPERLINK(),-5.0"


def test_rate_limiter_window():
    limiter = RateLimiter()

    assert limiter.allow("ana", 2, now=0) and limiter.allow("ana", 2, now=1)
    assert not limiter.allow("ana", 2, now=2)
    assert limiter.allow("beto", 2, now=2)
    assert limiter.allow("ana", 2, now=61)


@pytest.fixture
def client(client_with_model_path, pipeline_path):
    with client_with_model_path(pipeline_path) as client:
        yield client


def test_prediction_has_risk_level_and_explanation(client):
    response = client.post(
        "/api/v1/predict?explain=true", json={"transactions": [make_transaction()]}
    )

    body = response.json()
    [prediction] = body["predictions"]
    assert prediction["risk_level"] in {"low", "medium", "high"}
    assert body["risk_levels"]["high"] == body["threshold"]
    features = {c["feature"] for c in prediction["explanation"]}
    assert {"type", "amount"} <= features


def test_prediction_without_explanation_by_default(client):
    response = client.post(
        "/api/v1/predict", json={"transactions": [make_transaction()]}
    )

    assert response.json()["predictions"][0]["explanation"] is None


def test_rate_limit_returns_429(client, monkeypatch):
    from config.settings import settings
    from utils.rate_limit import limiter

    monkeypatch.setattr(settings, "rate_limit_per_minute", 1)
    limiter.hits.clear()
    payload = {"transactions": [make_transaction()]}

    assert client.post("/api/v1/predict", json=payload).status_code == 200
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 429
    assert response.headers["retry-after"] == "60"

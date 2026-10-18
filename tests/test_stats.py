from datetime import date

import pandas as pd
import pytest

from app.batch.usecases.use_batch_stats import batch_stats
from tests.factories import InMemoryBatchRepository, make_transaction
from utils.auth import get_current_user
from utils.password import hash_password


@pytest.fixture
def client(client_with_model_path, pipeline_path):
    with client_with_model_path(pipeline_path) as client:
        users = client.app.state.users
        users.save("jefe", hash_password("admin1234"), "admin")
        users.save("ana", hash_password("ana12345"))
        yield client


def act_as(client, username):
    client.app.dependency_overrides[get_current_user] = lambda: username


def upload(client, rows=2):
    content = pd.DataFrame([make_transaction() for _ in range(rows)])
    client.post(
        "/api/v1/predict/csv",
        files={"file": ("pagos.csv", content.to_csv(index=False).encode(), "text/csv")},
    )


def test_stats_counts_own_batches(client):
    act_as(client, "ana")
    upload(client, rows=3)
    act_as(client, "jefe")
    upload(client, rows=2)

    act_as(client, "ana")
    stats = client.get("/api/v1/batches/stats").json()

    assert (stats["batches"], stats["total_rows"]) == (1, 3)
    assert len(stats["days"]) == 14
    assert stats["days"][-1]["total_rows"] == 3


def test_admin_stats_for_everyone(client):
    act_as(client, "ana")
    upload(client, rows=3)
    act_as(client, "jefe")
    upload(client, rows=2)

    stats = client.get("/api/v1/batches/stats?all=true&days=7").json()

    assert (stats["batches"], stats["total_rows"]) == (2, 5)
    assert len(stats["days"]) == 7


def test_normal_user_cannot_see_everyone_stats(client):
    act_as(client, "ana")

    assert client.get("/api/v1/batches/stats?all=true").status_code == 403


@pytest.mark.parametrize("days", [0, 91])
def test_stats_rejects_invalid_days(client, days):
    act_as(client, "ana")

    assert client.get(f"/api/v1/batches/stats?days={days}").status_code == 422


def test_stats_fills_empty_days():
    stats = batch_stats(InMemoryBatchRepository(), None, 3, today=date(2026, 10, 17))

    assert [d.day for d in stats.days] == [
        date(2026, 10, 15),
        date(2026, 10, 16),
        date(2026, 10, 17),
    ]
    assert stats.batches == 0


def test_stats_rejects_unknown_timezone(client):
    act_as(client, "ana")

    response = client.get("/api/v1/batches/stats?tz=Marte/Base")

    assert response.status_code == 422


def test_stats_uses_timezone(client):
    act_as(client, "ana")
    upload(client)

    stats = client.get("/api/v1/batches/stats?tz=America/Lima").json()

    assert stats["days"][-1]["total_rows"] == 2

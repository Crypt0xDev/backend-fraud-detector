import os
import uuid
from datetime import date, timedelta

import pytest
from psycopg_pool import ConnectionPool

from app.batch.batch_repository import BatchRepository
from app.prediction.prediction_repository import PredictionRepository
from app.prediction.prediction_schema import Prediction, Transaction
from app.user.user_repository import UserRepository
from tests.factories import make_transaction

DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL, reason="Define TEST_DATABASE_URL para probar contra PostgreSQL"
)


@pytest.fixture
def users():
    pool = ConnectionPool(
        DATABASE_URL, kwargs={"autocommit": True, "prepare_threshold": None}
    )
    repository = UserRepository(pool)
    repository.init_schema()
    BatchRepository(pool).init_schema()
    username = f"pytest-{uuid.uuid4().hex[:8]}"
    yield repository, username
    with pool.connection() as conn:
        conn.execute("DELETE FROM users WHERE username = %s", (username,))
    pool.close()


def test_save_and_read(users):
    repository, username = users

    assert not repository.exists(username)
    assert repository.save(username, "hash-1") is True
    assert repository.get_password_hash(username) == "hash-1"


def test_save_updates_password(users):
    repository, username = users
    repository.save(username, "hash-1")

    assert repository.save(username, "hash-2") is False
    assert repository.get_password_hash(username) == "hash-2"


def test_batches_belong_to_user(users):
    repository, username = users
    repository.save(username, "hash")
    batches = BatchRepository(repository.pool)
    batch_id = uuid.uuid4()

    batches.add(batch_id, username, "pagos.csv", 10, 2, 0.5)

    assert [b.id for b in batches.list(username)] == [batch_id]
    assert batches.get("otro-usuario", batch_id) is None
    batches.delete(username, batch_id)
    assert batches.get(username, batch_id) is None


def test_batches_paginate(users):
    repository, username = users
    repository.save(username, "hash")
    batches = BatchRepository(repository.pool)
    ids = [uuid.uuid4() for _ in range(3)]
    for batch_id in ids:
        batches.add(batch_id, username, "pagos.csv", 10, 2, 0.5)

    first = batches.list(username, limit=2)
    rest = batches.list(username, limit=2, offset=2)

    assert batches.count(username) == 3
    assert batches.count("otro-usuario") == 0
    assert [b.id for b in first + rest] == ids[::-1]


def test_role_defaults_to_user_and_can_change(users):
    repository, username = users
    repository.save(username, "hash")

    assert repository.get_role(username) == "user"
    repository.set_role(username, "admin")
    assert repository.get_role(username) == "admin"
    repository.save(username, "hash-2")
    assert repository.get_role(username) == "admin"


def test_admin_queries(users):
    repository, username = users
    repository.save(username, "hash", "admin")
    batches = BatchRepository(repository.pool)
    batch_id = uuid.uuid4()
    batches.add(batch_id, username, "pagos.csv", 10, 2, 0.5)

    assert username in [u.username for u in repository.list()]
    assert repository.count_admins() >= 1
    assert batch_id in [b.id for b in batches.list(None, limit=1000)]
    assert batches.get(None, batch_id).username == username
    assert batches.ids(username) == [batch_id]

    repository.delete(username)

    assert not repository.exists(username)
    assert batches.get(None, batch_id) is None


def test_batch_stats(users):
    repository, username = users
    repository.save(username, "hash")
    batches = BatchRepository(repository.pool)
    batches.add(uuid.uuid4(), username, "a.csv", 10, 2, 0.5)
    batches.add(uuid.uuid4(), username, "b.csv", 5, 1, 0.5)

    assert batches.totals(username) == (2, 15, 3)
    [day] = batches.per_day(username, date.today() - timedelta(days=2), "UTC")
    assert (day.batches, day.total_rows, day.flagged_rows) == (2, 15, 3)


def test_prediction_history(users):
    repository, username = users
    repository.save(username, "hash")
    predictions = PredictionRepository(repository.pool)
    predictions.init_schema()
    transactions = [
        Transaction(**make_transaction()),
        Transaction(**make_transaction(type="PAYMENT")),
    ]
    results = [
        Prediction(fraud_probability=0.9, is_fraud=True),
        Prediction(fraud_probability=0.1, is_fraud=False),
    ]

    predictions.add_many(username, transactions, results, 0.5)

    assert predictions.totals(username) == (2, 1)
    assert {p.type for p in predictions.recent(username, 5)} == {"TRANSFER", "PAYMENT"}

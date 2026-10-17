import os
import uuid

import pytest
from psycopg_pool import ConnectionPool

from app.batch.batch_repository import BatchRepository
from app.user.user_repository import UserRepository

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

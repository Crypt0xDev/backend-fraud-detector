from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.batch.batch_schema import BatchDayOut, BatchOut
from app.user.user_schema import UserAccountOut
from utils.storage import StorageError

NUMERIC = ["step", "amount", "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest"]


class InMemoryUserRepository:
    def __init__(self):
        self.users = {}
        self.roles = {}

    def get_password_hash(self, username):
        return self.users.get(username)

    def get_role(self, username):
        return self.roles.get(username)

    def exists(self, username):
        return username in self.users

    def save(self, username, password_hash, role="user"):
        created = username not in self.users
        self.users[username] = password_hash
        if created:
            self.roles[username] = role
        return created

    def set_role(self, username, role):
        if username in self.users:
            self.roles[username] = role

    def list(self):
        return [
            UserAccountOut(
                username=name, role=self.roles[name], created_at=datetime.now(UTC)
            )
            for name in self.users
        ]

    def count_admins(self):
        return sum(role == "admin" for role in self.roles.values())

    def delete(self, username):
        self.users.pop(username, None)
        self.roles.pop(username, None)


class InMemoryBatchRepository:
    def __init__(self):
        self.rows = {}

    def add(self, batch_id, username, file_name, total_rows, flagged_rows, threshold):
        self.rows[batch_id] = (
            username,
            BatchOut(
                id=batch_id,
                username=username,
                file_name=file_name,
                total_rows=total_rows,
                flagged_rows=flagged_rows,
                threshold=threshold,
                created_at=datetime.now(UTC),
            ),
        )

    def list(self, username, limit=50, offset=0):
        batches = [
            batch
            for owner, batch in self.rows.values()
            if username is None or owner == username
        ]
        batches = sorted(batches, key=lambda b: b.created_at, reverse=True)
        return batches[offset : None if limit is None else offset + limit]

    def count(self, username):
        return len(self.list(username, limit=None))

    def get(self, username, batch_id):
        owner, batch = self.rows.get(batch_id, (None, None))
        return batch if batch and (username is None or owner == username) else None

    def totals(self, username):
        batches = self.list(username, limit=None)
        return (
            len(batches),
            sum(b.total_rows for b in batches),
            sum(b.flagged_rows for b in batches),
        )

    def per_day(self, username, since, tz):
        days = {}
        for batch in self.list(username, limit=None):
            day = batch.created_at.astimezone(ZoneInfo(tz)).date()
            if day < since:
                continue
            current = days.setdefault(
                day, BatchDayOut(day=day, batches=0, total_rows=0, flagged_rows=0)
            )
            current.batches += 1
            current.total_rows += batch.total_rows
            current.flagged_rows += batch.flagged_rows
        return sorted(days.values(), key=lambda d: d.day)

    def ids(self, username):
        return [
            batch_id for batch_id, (owner, _) in self.rows.items() if owner == username
        ]

    def delete(self, username, batch_id):
        if self.get(username, batch_id):
            del self.rows[batch_id]


class InMemoryStorage:
    def __init__(self):
        self.objects = {}
        self.fail = False

    def upload(self, path, content, content_type):
        if self.fail:
            raise StorageError("fallo simulado")
        self.objects[path] = content

    def signed_url(self, path, expires_in, download_name):
        return f"https://storage.test/{path}?download={download_name}"

    def delete(self, paths):
        for path in paths:
            self.objects.pop(path, None)


def make_transaction(**overrides):
    transaction = {
        "step": 1,
        "type": "TRANSFER",
        "amount": 1000.0,
        "nameOrig": "C123",
        "oldbalanceOrg": 1000.0,
        "newbalanceOrig": 0.0,
        "nameDest": "C456",
        "oldbalanceDest": 0.0,
        "newbalanceDest": 0.0,
    }
    return transaction | overrides


def save_pipeline(path, extra_columns=()):
    rows = pd.DataFrame(
        [
            make_transaction(),
            make_transaction(type="PAYMENT", amount=10.0, newbalanceOrig=990.0),
            make_transaction(type="CASH_OUT", amount=5000.0, oldbalanceOrg=5000.0),
            make_transaction(type="CASH_IN", amount=50.0, newbalanceOrig=1050.0),
        ]
    )
    for column in extra_columns:
        rows[column] = 0.0
    rows = rows[["type", *NUMERIC, *extra_columns]]

    pipeline = Pipeline(
        [
            (
                "preprocess",
                ColumnTransformer(
                    [("type", OneHotEncoder(handle_unknown="ignore"), ["type"])],
                    remainder="passthrough",
                ),
            ),
            ("model", LogisticRegression()),
        ]
    )
    pipeline.fit(rows, [1, 0, 1, 0])
    joblib.dump(pipeline, path)
    return path

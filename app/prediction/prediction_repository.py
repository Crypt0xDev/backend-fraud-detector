from typing import Any
from uuid import uuid4

from app.prediction.prediction_schema import (
    Prediction,
    PredictionRecordOut,
    Transaction,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY,
    username TEXT NOT NULL REFERENCES users (username) ON DELETE CASCADE,
    type TEXT NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    name_orig TEXT,
    name_dest TEXT,
    fraud_probability DOUBLE PRECISION NOT NULL,
    is_fraud BOOLEAN NOT NULL,
    threshold DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS predictions_username_created_at
    ON predictions (username, created_at DESC);
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
"""

COLUMNS = (
    "id, username, type, amount, name_orig, name_dest, fraud_probability, "
    "is_fraud, threshold, created_at"
)
FIELDS = (
    "id",
    "username",
    "type",
    "amount",
    "name_orig",
    "name_dest",
    "fraud_probability",
    "is_fraud",
    "threshold",
    "created_at",
)


class PredictionRepository:
    def __init__(self, pool: Any):
        self.pool = pool

    def init_schema(self) -> None:
        with self.pool.connection() as conn:
            conn.execute(SCHEMA)

    def add_many(
        self,
        username: str,
        transactions: list[Transaction],
        predictions: list[Prediction],
        threshold: float,
    ) -> None:
        rows = [
            (
                uuid4(),
                username,
                t.type,
                t.amount,
                t.nameOrig,
                t.nameDest,
                p.fraud_probability,
                p.is_fraud,
                threshold,
            )
            for t, p in zip(transactions, predictions, strict=True)
        ]
        with self.pool.connection() as conn:
            conn.cursor().executemany(
                f"INSERT INTO predictions ({COLUMNS.rsplit(', ', 1)[0]}) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                rows,
            )

    def recent(
        self, owner: str | None, limit: int, offset: int = 0, alerts_only: bool = False
    ) -> list[PredictionRecordOut]:
        where, params = owner_filter(owner, alerts_only)
        with self.pool.connection() as conn:
            rows = conn.execute(
                f"SELECT {COLUMNS} FROM predictions {where} "
                "ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (*params, limit, offset),
            ).fetchall()
        return [PredictionRecordOut(**dict(zip(FIELDS, row))) for row in rows]

    def totals(self, owner: str | None) -> tuple[int, int]:
        where, params = owner_filter(owner)
        with self.pool.connection() as conn:
            row = conn.execute(
                "SELECT count(*), count(*) FILTER (WHERE is_fraud) "
                f"FROM predictions {where}",
                params,
            ).fetchone()
        return (row[0], row[1]) if row else (0, 0)


def owner_filter(owner: str | None, alerts_only: bool = False) -> tuple[str, tuple]:
    clauses = (["username = %s"] if owner is not None else []) + (
        ["is_fraud"] if alerts_only else []
    )
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return where, (owner,) if owner is not None else ()

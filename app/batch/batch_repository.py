from uuid import UUID
from typing import Any

from app.batch.batch_schema import BatchOut

SCHEMA = """
CREATE TABLE IF NOT EXISTS batches (
    id UUID PRIMARY KEY,
    username TEXT NOT NULL REFERENCES users (username) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    total_rows INTEGER NOT NULL,
    flagged_rows INTEGER NOT NULL,
    threshold DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS batches_username_created_at
    ON batches (username, created_at DESC);
ALTER TABLE batches ENABLE ROW LEVEL SECURITY;
"""

COLUMNS = "id, file_name, total_rows, flagged_rows, threshold, created_at"
FIELDS = ("id", "file_name", "total_rows", "flagged_rows", "threshold", "created_at")


class BatchRepository:
    def __init__(self, pool: Any):
        self.pool = pool

    def init_schema(self) -> None:
        with self.pool.connection() as conn:
            conn.execute(SCHEMA)

    def add(
        self,
        batch_id: UUID,
        username: str,
        file_name: str,
        total_rows: int,
        flagged_rows: int,
        threshold: float,
    ) -> None:
        with self.pool.connection() as conn:
            conn.execute(
                "INSERT INTO batches (id, username, file_name, total_rows, "
                "flagged_rows, threshold) VALUES (%s, %s, %s, %s, %s, %s)",
                (batch_id, username, file_name, total_rows, flagged_rows, threshold),
            )

    def list(self, username: str, limit: int = 50) -> list[BatchOut]:
        with self.pool.connection() as conn:
            rows = conn.execute(
                f"SELECT {COLUMNS} FROM batches WHERE username = %s "
                "ORDER BY created_at DESC LIMIT %s",
                (username, limit),
            ).fetchall()
            return [BatchOut(**dict(zip(FIELDS, row))) for row in rows]

    def get(self, username: str, batch_id: UUID) -> BatchOut | None:
        with self.pool.connection() as conn:
            row = conn.execute(
                f"SELECT {COLUMNS} FROM batches WHERE username = %s AND id = %s",
                (username, batch_id),
            ).fetchone()
            return BatchOut(**dict(zip(FIELDS, row))) if row is not None else None

    def delete(self, username: str, batch_id: UUID) -> None:
        with self.pool.connection() as conn:
            conn.execute(
                "DELETE FROM batches WHERE username = %s AND id = %s",
                (username, batch_id),
            )

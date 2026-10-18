from datetime import date
from typing import Any
from uuid import UUID

from app.batch.batch_schema import BatchDayOut, BatchOut

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

COLUMNS = "id, username, file_name, total_rows, flagged_rows, threshold, created_at"
FIELDS = (
    "id",
    "username",
    "file_name",
    "total_rows",
    "flagged_rows",
    "threshold",
    "created_at",
)


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

    def list(
        self, owner: str | None, limit: int = 50, offset: int = 0
    ) -> list[BatchOut]:
        """Lotes de `owner`, o de todos los usuarios si es None."""
        where, params = owner_filter(owner)
        with self.pool.connection() as conn:
            rows = conn.execute(
                f"SELECT {COLUMNS} FROM batches {where} "
                "ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s",
                (*params, limit, offset),
            ).fetchall()
            return [BatchOut(**dict(zip(FIELDS, row))) for row in rows]

    def count(self, owner: str | None) -> int:
        where, params = owner_filter(owner)
        with self.pool.connection() as conn:
            row = conn.execute(
                f"SELECT count(*) FROM batches {where}", params
            ).fetchone()
        return row[0] if row else 0

    def get(self, owner: str | None, batch_id: UUID) -> BatchOut | None:
        where, params = owner_filter(owner, "id = %s")
        with self.pool.connection() as conn:
            row = conn.execute(
                f"SELECT {COLUMNS} FROM batches {where}", (*params, batch_id)
            ).fetchone()
            return BatchOut(**dict(zip(FIELDS, row))) if row is not None else None

    def totals(self, owner: str | None) -> tuple[int, int, int]:
        where, params = owner_filter(owner)
        with self.pool.connection() as conn:
            row = conn.execute(
                "SELECT count(*), coalesce(sum(total_rows), 0), "
                f"coalesce(sum(flagged_rows), 0) FROM batches {where}",
                params,
            ).fetchone()
        return (row[0], row[1], row[2]) if row else (0, 0, 0)

    def per_day(self, owner: str | None, since: date, tz: str) -> list[BatchDayOut]:
        """Lotes agrupados por día en la zona `tz` desde `since`, sin los días vacíos."""
        where, params = owner_filter(owner, "(created_at AT TIME ZONE %s)::date >= %s")
        with self.pool.connection() as conn:
            rows = conn.execute(
                "SELECT (created_at AT TIME ZONE %s)::date AS day, count(*), "
                f"sum(total_rows), sum(flagged_rows) FROM batches {where} "
                "GROUP BY day ORDER BY day",
                (tz, *params, tz, since),
            ).fetchall()
        return [
            BatchDayOut(day=d, batches=b, total_rows=t, flagged_rows=f)
            for d, b, t, f in rows
        ]

    def ids(self, username: str) -> list[UUID]:
        with self.pool.connection() as conn:
            rows = conn.execute(
                "SELECT id FROM batches WHERE username = %s", (username,)
            ).fetchall()
            return [row[0] for row in rows]

    def delete(self, owner: str | None, batch_id: UUID) -> None:
        where, params = owner_filter(owner, "id = %s")
        with self.pool.connection() as conn:
            conn.execute(f"DELETE FROM batches {where}", (*params, batch_id))


def owner_filter(owner: str | None, *conditions: str) -> tuple[str, tuple]:
    clauses = (["username = %s"] if owner is not None else []) + list(conditions)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return where, (owner,) if owner is not None else ()

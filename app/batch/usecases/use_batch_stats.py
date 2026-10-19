from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.batch.batch_entity import Batch
from app.batch.batch_schema import BatchDayOut, BatchStatsOut
from app.batch.batch_scope import requested_by
from app.user.user_entity import User


def execute(
    db: Session,
    current_user: User,
    all: bool,
    days: int,
    tz: str = "UTC",
    today: date | None = None,
) -> BatchStatsOut:
    """Totales y lotes por día de los últimos `days` días"""
    try:
        zone = ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Zona horaria no válida: {tz}",
        ) from error
    owner = requested_by(current_user, all)
    today = today or datetime.now(zone).date()
    since = today - timedelta(days=days - 1)

    # El día se calcula en Python y no en SQL para que funcione en cualquier base
    series = {
        since + timedelta(days=i): BatchDayOut(
            day=since + timedelta(days=i), batches=0, total_rows=0, flagged_rows=0
        )
        for i in range(days)
    }
    start = datetime.combine(since, time.min, zone).astimezone(UTC)
    rows = (
        db.query(Batch.created_at, Batch.total_rows, Batch.flagged_rows)
        .filter(*owner, Batch.created_at >= start)
        .all()
    )
    for created_at, total_rows, flagged_rows in rows:
        aware = created_at if created_at.tzinfo else created_at.replace(tzinfo=UTC)
        day = series.get(aware.astimezone(zone).date())
        if day is not None:
            day.batches += 1
            day.total_rows += total_rows
            day.flagged_rows += flagged_rows

    batches, total_rows, flagged_rows = (
        db.query(
            func.count(Batch.id),
            func.coalesce(func.sum(Batch.total_rows), 0),
            func.coalesce(func.sum(Batch.flagged_rows), 0),
        )
        .filter(*owner)
        .one()
    )
    return BatchStatsOut(
        batches=batches,
        total_rows=total_rows,
        flagged_rows=flagged_rows,
        days=list(series.values()),
    )

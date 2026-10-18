from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.batch.batch_repository import BatchRepository
from app.batch.batch_schema import BatchDayOut, BatchStatsOut


def batch_stats(
    batches: BatchRepository,
    owner: str | None,
    days: int,
    tz: str = "UTC",
    today: date | None = None,
) -> BatchStatsOut:
    """Totales de `owner` (todos si es None) y una serie diaria de `days` días, en la
    zona horaria `tz`, con los días sin lotes en cero."""
    today = today or datetime.now(ZoneInfo(tz)).date()
    since = today - timedelta(days=days - 1)
    found = {day.day: day for day in batches.per_day(owner, since, tz)}
    series = [
        found.get(d, BatchDayOut(day=d, batches=0, total_rows=0, flagged_rows=0))
        for d in (since + timedelta(days=i) for i in range(days))
    ]
    total_batches, total_rows, flagged_rows = batches.totals(owner)
    return BatchStatsOut(
        batches=total_batches,
        total_rows=total_rows,
        flagged_rows=flagged_rows,
        days=series,
    )

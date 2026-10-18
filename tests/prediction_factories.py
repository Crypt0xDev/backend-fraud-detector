from datetime import UTC, datetime
from uuid import uuid4

from app.prediction.prediction_schema import PredictionRecordOut


class InMemoryPredictionRepository:
    def __init__(self):
        self.rows = []
        self.fail = False

    def add_many(self, username, transactions, predictions, threshold):
        if self.fail:
            raise RuntimeError("fallo simulado")
        for t, p in zip(transactions, predictions, strict=True):
            self.rows.append(
                PredictionRecordOut(
                    id=uuid4(),
                    username=username,
                    type=t.type,
                    amount=t.amount,
                    name_orig=t.nameOrig,
                    name_dest=t.nameDest,
                    fraud_probability=p.fraud_probability,
                    is_fraud=p.is_fraud,
                    threshold=threshold,
                    created_at=datetime.now(UTC),
                )
            )

    def _owned(self, owner):
        return [r for r in self.rows if owner is None or r.username == owner]

    def recent(self, owner, limit, offset=0, alerts_only=False):
        rows = [r for r in self._owned(owner) if r.is_fraud or not alerts_only]
        rows = sorted(rows, key=lambda r: r.created_at, reverse=True)
        return rows[offset : offset + limit]

    def totals(self, owner):
        rows = self._owned(owner)
        return len(rows), sum(r.is_fraud for r in rows)

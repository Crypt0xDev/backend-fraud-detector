from sqlalchemy.orm import Session

from app.batch.batch_entity import Batch
from app.batch.batch_schema import BatchOut, BatchPageOut
from app.batch.batch_scope import requested_by
from app.user.user_entity import User


def execute(
    db: Session, current_user: User, all: bool, page: int, page_size: int
) -> BatchPageOut:
    query = db.query(Batch).filter(*requested_by(current_user, all))
    batches = (
        query.order_by(Batch.created_at.desc(), Batch.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return BatchPageOut(
        items=[BatchOut.model_validate(b, from_attributes=True) for b in batches],
        total=query.count(),
        page=page,
        page_size=page_size,
    )

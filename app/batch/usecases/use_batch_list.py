from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.batch.batch_entity import Batch
from app.batch.batch_schema import BatchOut, BatchPageOut
from app.batch.batch_scope import requested_by
from app.user.user_entity import User


def execute(
    db: Session, current_user: User, all: bool, page: int, page_size: int
) -> BatchPageOut:
    query = select(Batch).where(*requested_by(current_user, all))
    batches = db.scalars(
        query.order_by(Batch.created_at.desc(), Batch.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return BatchPageOut(
        items=[BatchOut.model_validate(b, from_attributes=True) for b in batches],
        total=db.scalar(select(func.count()).select_from(query.subquery())) or 0,
        page=page,
        page_size=page_size,
    )

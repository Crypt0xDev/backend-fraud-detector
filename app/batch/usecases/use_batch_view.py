from uuid import UUID

from sqlalchemy.orm import Session

from app.batch.batch_entity import Batch
from app.batch.batch_scope import visible_to
from app.user.user_entity import User


def execute(db: Session, current_user: User, batch_id: UUID) -> Batch | None:
    return (
        db.query(Batch).filter(*visible_to(current_user), Batch.id == batch_id).first()
    )

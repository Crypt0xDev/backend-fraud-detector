from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.batch.batch_entity import Batch
from app.batch.batch_scope import visible_to
from app.user.user_entity import User


def execute(db: Session, current_user: User, batch_id: UUID) -> Batch | None:
    """El lote, si el usuario lo puede ver; si no, None (no se dice si existe)"""
    return db.scalars(select(Batch).where(*visible_to(current_user), Batch.id == batch_id)).first()

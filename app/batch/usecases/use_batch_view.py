from uuid import UUID

from sqlalchemy.orm import Session

from app.batch.batch_entity import Batch
from app.batch.batch_scope import visible_to
from app.user.user_entity import User
from utils.errors import NotFoundError


def execute(db: Session, current_user: User, batch_id: UUID) -> Batch:
    """El lote, si el usuario lo puede ver; si no, NotFoundError (no se dice si existe)"""
    batch = (
        db.query(Batch).filter(*visible_to(current_user), Batch.id == batch_id).first()
    )
    if batch is None:
        raise NotFoundError("El lote no existe")
    return batch

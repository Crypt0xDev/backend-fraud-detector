from sqlalchemy import select
from sqlalchemy.orm import Session

from app.user.user_entity import User
from app.user.user_schema import ACTIVE, DISABLED
from utils.helpers import utcnow


def execute(db: Session, username: str) -> bool:
    user = db.scalars(select(User).where(User.username == username, User.state == DISABLED)).first()

    if user is None:
        return False

    user.state = ACTIVE
    user.updated_at = utcnow()
    db.commit()
    return True

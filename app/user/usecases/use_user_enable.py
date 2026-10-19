from sqlalchemy.orm import Session

from app.user.user_entity import User
from app.user.user_schema import ACTIVE
from utils.helpers import utcnow


def execute(db: Session, current_user: User, username: str) -> bool:
    db_user = (
        db.query(User).filter(User.username == username, User.state != ACTIVE).first()
    )
    if db_user is None:
        return False

    db_user.state = ACTIVE
    db_user.updated_at = utcnow()
    db.commit()
    return True

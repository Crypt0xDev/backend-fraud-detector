from sqlalchemy.orm import Session

from app.user.usecases.use_user_roles import user_not_found
from app.user.user_entity import User


def execute(db: Session, username: str) -> User:
    db_user = db.query(User).filter(User.username == username).first()
    if db_user is None:
        raise user_not_found()
    return db_user

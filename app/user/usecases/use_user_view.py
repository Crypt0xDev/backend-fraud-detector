from sqlalchemy.orm import Session

from app.user.user_entity import User


def execute(db: Session, current_user: User, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()

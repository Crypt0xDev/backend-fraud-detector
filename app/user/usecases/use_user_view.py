from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.user.user_entity import User
from app.user.user_schema import DELETED


def execute(db: Session, username: str) -> User | None:
    return db.scalars(select(User).options(selectinload(User.roles)).where(User.username == username, User.state != DELETED)).first()

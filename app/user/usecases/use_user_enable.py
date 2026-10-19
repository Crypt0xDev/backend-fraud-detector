from sqlalchemy.orm import Session

from app.user.usecases.use_user_roles import user_not_found
from app.user.user_entity import User
from app.user.user_schema import ACTIVE
from utils.helpers import utcnow


def execute(db: Session, username: str) -> None:
    db_user = (
        db.query(User).filter(User.username == username, User.state != ACTIVE).first()
    )
    if db_user is None:
        raise user_not_found("Usuario no encontrado o ya está habilitado")

    db_user.state = ACTIVE
    db_user.updated_at = utcnow()
    db.commit()

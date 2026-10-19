from sqlalchemy.orm import Session

from app.user.usecases.use_user_roles import user_not_found
from app.user.user_entity import User
from app.user.user_schema import SchemaChangePassword
from utils.errors import InvalidRequestError
from utils.helpers import utcnow
from utils.password import hash_password, verify_password


def execute(db: Session, current_user: User, data: SchemaChangePassword) -> None:
    db_user = db.query(User).filter(User.username == current_user.username).first()
    if db_user is None:
        raise user_not_found()

    # Verificar la contraseña actual
    if not verify_password(data.current_password, db_user.password_hash):
        raise InvalidRequestError("La contraseña actual no es correcta")

    db_user.password_hash = hash_password(data.new_password)
    db_user.token_version += 1
    db_user.updated_at = utcnow()
    db.commit()

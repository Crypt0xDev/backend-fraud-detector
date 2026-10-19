import logging

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.role.role_entity import Role
from app.role.role_schema import ANALYST_ROLE
from app.user.user_entity import User
from app.user.user_schema import ACTIVE, SchemaCreate
from utils.password import hash_password

logger = logging.getLogger(__name__)


def seed_account(
    db: Session,
    username: str | None,
    password: str | None,
    *,
    root: bool,
    env_prefix: str,
) -> None:
    """Crea la cuenta si no existe; no cambia su contraseña"""
    if not username or not password:
        return

    user = db.query(User).filter(User.username == username).first()
    if user:
        if root and not user.root:
            user.root = True
            db.commit()
            logger.info("✅ Usuario %s ahora es root", username)
        else:
            logger.info("ℹ️  Usuario %s: ya existe", username)
        return

    try:
        account = SchemaCreate(username=username, password=password, root=root)
    except ValidationError as error:
        logger.error(
            "⚠️  %s_USERNAME/%s_PASSWORD no válidos: %s", env_prefix, env_prefix, error
        )
        return

    user = User(
        username=account.username,
        password_hash=hash_password(account.password),
        root=account.root,
        state=ACTIVE,
    )
    if not root:
        user.roles = db.query(Role).filter(Role.name == ANALYST_ROLE).all()
    db.add(user)
    db.commit()
    logger.info("✅ Usuario %s creado (%s)", username, "root" if root else ANALYST_ROLE)

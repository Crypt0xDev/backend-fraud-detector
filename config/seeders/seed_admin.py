import logging

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.user.usecases.use_user_create import username_taken
from app.user.user_entity import User
from app.user.user_schema import ACTIVE, SchemaCreate
from config.settings import settings
from utils.password import hash_password

logger = logging.getLogger(__name__)

def seed_admin(db: Session) -> None:
    """Crea el root de ADMIN_USERNAME / ADMIN_PASSWORD solo si la base no tiene
    ninguno activo. Así un admin borrado o sin root no revive al reiniciar si hay
    otro root; los demás usuarios los crea el admin desde la API"""
    username, password = settings.admin_username, settings.admin_password
    if not username or not password:
        return
    # Un root deshabilitado o eliminado no puede entrar, así que no cuenta
    if db.scalar(select(User.username).where(User.root, User.state == ACTIVE).limit(1)):
        logger.debug("ℹ️  Ya hay un usuario root")
        return

    try:
        account = SchemaCreate(username=username, password=password, root=True)
    except ValidationError as error:
        logger.error("⚠️  ADMIN_USERNAME/ADMIN_PASSWORD no válidos: %s", error)
        return

    if username_taken(db, account.username):
        logger.error(
            "⚠️  No hay root y %s ya existe: usa python -m app.user.create_user %s --role admin",
            username,
            username,
        )
        return

    db.add(
        User(
            username=account.username,
            password_hash=hash_password(account.password),
            root=True,
            state=ACTIVE,
        )
    )
    db.commit()
    logger.info("✅ Usuario %s creado (root)", username)

import logging

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.role.role_entity import Role
from app.role.role_schema import ANALYST_ROLE
from app.user.user_entity import UserRole

logger = logging.getLogger(__name__)


def seed_legacy_roles(db: Session) -> None:
    """Pasa los usuarios de la versión anterior (columna role) a los nuevos roles"""
    columns = {column["name"] for column in inspect(db.get_bind()).get_columns("users")}
    if "role" not in columns:
        return

    analyst = db.query(Role).filter(Role.name == ANALYST_ROLE).one()
    db.execute(text("UPDATE users SET root = (role = 'admin')"))
    usernames = db.execute(text("SELECT username FROM users WHERE role <> 'admin'"))
    migrated = 0
    for (username,) in usernames.all():
        db.add(UserRole(username=username, role_id=analyst.id))
        migrated += 1
    db.execute(text("ALTER TABLE users DROP COLUMN role"))
    db.commit()
    logger.info(
        "✅ Usuarios migrados a roles: admin → root, %s con rol %s",
        migrated,
        ANALYST_ROLE,
    )

"""Crea un usuario, o cambia su contraseña y lo reactiva: python -m app.user.create_user <usuario>"""

import argparse
import getpass
import sys

from sqlalchemy import select

from app.role.role_schema import ANALYST_ROLE
from app.user.usecases.use_user_create import username_taken
from app.user.user_schema import ACTIVE, check_username
from config.database import SessionLocal, engine, init_db
from config.entities import Role, User
from utils.password import MIN_PASSWORD_LENGTH, hash_password

# admin = root; user = rol Analista
ROLES = ("admin", "user")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("username")
    parser.add_argument(
        "--role",
        choices=ROLES,
        help="admin = root; user = rol Analista (por defecto al crearlo; si existe, no cambia)",
    )
    args = parser.parse_args()
    username = args.username.strip()
    try:
        check_username(username)
    except ValueError as error:
        sys.exit(str(error))

    password = getpass.getpass("Contraseña: ")
    if getpass.getpass("Repite la contraseña: ") != password:
        sys.exit("Las contraseñas no coinciden")
    if len(password) < MIN_PASSWORD_LENGTH:
        sys.exit(f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres")

    if engine is None:
        sys.exit("Define DATABASE_URL en .env")
    try:
        init_db(engine)
        with SessionLocal() as db:
            user = db.get(User, username)
            created = user is None
            if created and username_taken(db, username):
                sys.exit(f"Ya existe un usuario {username} con otras mayúsculas")
            if user is None:
                user = User(username=username, root=args.role == "admin", state=ACTIVE)
                db.add(user)
            elif args.role:
                user.root = args.role == "admin"
            # Si estaba deshabilitado o eliminado, vuelve a poder entrar
            reactivated = user.state != ACTIVE
            user.state = ACTIVE
            user.deleted_at = None
            if not user.root and not user.roles:
                user.roles = list(db.scalars(select(Role).where(Role.name == ANALYST_ROLE)))
            user.password_hash = hash_password(password)
            if not created:
                user.token_version += 1
            db.commit()
    finally:
        engine.dispose()
    action = "creado" if created else "reactivado" if reactivated else "actualizado"
    print(f"Usuario {username} {action}")


if __name__ == "__main__":
    main()

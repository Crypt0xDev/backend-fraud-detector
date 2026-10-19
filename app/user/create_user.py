"""Crea un usuario o cambia su contraseña: python -m app.user.create_user <usuario>"""

import argparse
import getpass
import sys

from app.role.role_schema import ANALYST_ROLE
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
            user = db.query(User).filter(User.username == username).first()
            created = user is None
            if created:
                user = User(username=username, root=args.role == "admin", state=ACTIVE)
                db.add(user)
            elif args.role:
                user.root = args.role == "admin"
            if not user.root and not user.roles:
                user.roles = db.query(Role).filter(Role.name == ANALYST_ROLE).all()
            user.password_hash = hash_password(password)
            if not created:
                user.token_version += 1
            db.commit()
    finally:
        engine.dispose()
    print(f"Usuario {username} {'creado' if created else 'actualizado'}")


if __name__ == "__main__":
    main()

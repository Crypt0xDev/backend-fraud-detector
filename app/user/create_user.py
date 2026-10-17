"""Crea un usuario o cambia su contraseña: python -m app.user.create_user <usuario>"""

import argparse
import getpass
import sys

from app.user.usecases.use_user_create import InvalidUserError, create_user
from app.user.user_repository import UserRepository
from config.database import open_pool
from config.settings import settings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("username")
    username = parser.parse_args().username

    password = getpass.getpass("Contraseña: ")
    if getpass.getpass("Repite la contraseña: ") != password:
        sys.exit("Las contraseñas no coinciden")

    pool = open_pool(settings.database_url)
    if pool is None:
        sys.exit("Define DATABASE_URL en .env")
    try:
        users = UserRepository(pool)
        users.init_schema()
        created = create_user(users, username, password)
    except InvalidUserError as error:
        sys.exit(str(error))
    finally:
        pool.close()
    print(f"Usuario {username.strip()} {'creado' if created else 'actualizado'}")


if __name__ == "__main__":
    main()

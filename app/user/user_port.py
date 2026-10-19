from typing import Protocol

from sqlalchemy.orm import Session


class UserDataCleaner(Protocol):
    """Borra los archivos de un usuario antes de eliminar su cuenta"""

    def delete_user_data(self, db: Session, username: str) -> None: ...

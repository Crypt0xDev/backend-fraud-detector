from psycopg.rows import class_row
from psycopg_pool import ConnectionPool

from app.user.user_schema import DEFAULT_ROLE, Role, UserAccountOut

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT '{DEFAULT_ROLE}';
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role IN ('admin', 'user'));
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
"""


class UserRepository:
    def __init__(self, pool: ConnectionPool):
        self.pool = pool

    def init_schema(self) -> None:
        with self.pool.connection() as conn:
            conn.execute(SCHEMA)

    def get_password_hash(self, username: str) -> str | None:
        with self.pool.connection() as conn:
            row = conn.execute(
                "SELECT password_hash FROM users WHERE username = %s", (username,)
            ).fetchone()
        return row[0] if row else None

    def get_role(self, username: str) -> Role | None:
        with self.pool.connection() as conn:
            row = conn.execute(
                "SELECT role FROM users WHERE username = %s", (username,)
            ).fetchone()
        return row[0] if row else None

    def exists(self, username: str) -> bool:
        return self.get_password_hash(username) is not None

    def save(
        self, username: str, password_hash: str, role: Role = DEFAULT_ROLE
    ) -> bool:
        """Crea el usuario o actualiza su contraseña; devuelve True si es nuevo.
        El rol solo se asigna al crearlo; para cambiarlo, set_role."""
        with self.pool.connection() as conn:
            row = conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s) "
                "ON CONFLICT (username) DO UPDATE "
                "SET password_hash = EXCLUDED.password_hash "
                "RETURNING xmax = 0",
                (username, password_hash, role),
            ).fetchone()
        return bool(row and row[0])

    def set_role(self, username: str, role: Role) -> None:
        with self.pool.connection() as conn:
            conn.execute(
                "UPDATE users SET role = %s WHERE username = %s", (role, username)
            )

    def list(self) -> list[UserAccountOut]:
        with self.pool.connection() as conn:
            cursor = conn.cursor(row_factory=class_row(UserAccountOut))
            return cursor.execute(
                "SELECT username, role, created_at FROM users ORDER BY created_at"
            ).fetchall()

    def count_admins(self) -> int:
        with self.pool.connection() as conn:
            row = conn.execute(
                "SELECT count(*) FROM users WHERE role = 'admin'"
            ).fetchone()
        return row[0] if row else 0

    def delete(self, username: str) -> None:
        with self.pool.connection() as conn:
            conn.execute("DELETE FROM users WHERE username = %s", (username,))

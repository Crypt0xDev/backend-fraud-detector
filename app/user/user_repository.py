from psycopg_pool import ConnectionPool

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
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

    def exists(self, username: str) -> bool:
        return self.get_password_hash(username) is not None

    def save(self, username: str, password_hash: str) -> bool:
        """Crea el usuario o actualiza su contraseña; devuelve True si es nuevo."""
        with self.pool.connection() as conn:
            row = conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s) "
                "ON CONFLICT (username) DO UPDATE "
                "SET password_hash = EXCLUDED.password_hash "
                "RETURNING xmax = 0",
                (username, password_hash),
            ).fetchone()
        return bool(row and row[0])

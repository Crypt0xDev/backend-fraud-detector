from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from config.database import BaseModel
from app.user.user_schema import ACTIVE, DELETED, DISABLED
from utils.helpers import utcnow

if TYPE_CHECKING:
    from app.batch.batch_entity import Batch
    from app.prediction.prediction_entity import PredictionRecord
    from app.role.role_entity import Role

class User(BaseModel):
    """
    Credenciales de acceso al sistema.
    Regla: el root puede hacer todo; los demás tienen los permisos de sus roles.
    """
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(f"state IN ('{ACTIVE}', '{DISABLED}', '{DELETED}')", name="users_state_check"),
        {
            "info": {
                "upgrades": [
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS root BOOLEAN NOT NULL DEFAULT false",
                    f"ALTER TABLE users ADD COLUMN IF NOT EXISTS state TEXT NOT NULL DEFAULT '{ACTIVE}'",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ",
                    # Los estados pasaron de Activo/Inactivo a Activo/Deshabilitado/Eliminado
                    "ALTER TABLE users DROP CONSTRAINT IF EXISTS users_state_check",
                    f"UPDATE users SET state = '{DISABLED}' WHERE state = 'Inactivo'",
                    f"ALTER TABLE users ADD CONSTRAINT users_state_check CHECK (state IN ('{ACTIVE}', '{DISABLED}', '{DELETED}'))",
                    "ALTER TABLE users ENABLE ROW LEVEL SECURITY",
                ]
            }
        },
    )

    # Columnas
    username: Mapped[str] = mapped_column(Text, primary_key=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    # Flags de acceso especial
    root: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    # Estado del usuario
    state: Mapped[str] = mapped_column(Text, nullable=False, server_default=ACTIVE)
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relaciones
    roles: Mapped[list["Role"]] = relationship(secondary="user_role", order_by="Role.name")
    batches: Mapped[list["Batch"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    predictions: Mapped[list["PredictionRecord"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)

class UserRole(BaseModel):
    __tablename__ = "user_role"
    __table_args__ = (
        UniqueConstraint("username", "role_id", name="uq_user_role"),
        {"info": {"upgrades": ["ALTER TABLE user_role ENABLE ROW LEVEL SECURITY"]}},
    )

    # Columnas
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(Text, ForeignKey("users.username", ondelete="CASCADE"), nullable=False)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("role.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

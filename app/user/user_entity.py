from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.user.user_schema import ACTIVE
from config.database import BaseModel
from utils.helpers import utcnow

if TYPE_CHECKING:
    from app.batch.batch_entity import Batch
    from app.prediction.prediction_entity import PredictionRecord
    from app.role.role_entity import Role


class User(BaseModel):
    """Usuarios del sistema; el root puede hacer todo"""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("state IN ('Activo', 'Inactivo')", name="users_state_check"),
        {
            "info": {
                "upgrades": [
                    (
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS root BOOLEAN "
                        "NOT NULL DEFAULT false"
                    ),
                    (
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS state TEXT NOT NULL "
                        f"DEFAULT '{ACTIVE}'"
                    ),
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ",
                    (
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version "
                        "INTEGER NOT NULL DEFAULT 0"
                    ),
                    "ALTER TABLE users ENABLE ROW LEVEL SECURITY",
                ]
            }
        },
    )

    username: Mapped[str] = mapped_column(Text, primary_key=True)
    password_hash: Mapped[str] = mapped_column(Text)
    # Acceso total al sistema
    root: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    state: Mapped[str] = mapped_column(Text, server_default=ACTIVE)
    # Sube al cambiar la contraseña; los tokens con otro número ya no sirven
    token_version: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    roles: Mapped[list["Role"]] = relationship(
        secondary="user_role", order_by="Role.name"
    )
    batches: Mapped[list["Batch"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    predictions: Mapped[list["PredictionRecord"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )


class UserRole(BaseModel):
    """Los roles que tiene cada usuario"""

    __tablename__ = "user_role"
    __table_args__ = (
        UniqueConstraint("username", "role_id", name="uq_user_role"),
        {"info": {"upgrades": ["ALTER TABLE user_role ENABLE ROW LEVEL SECURITY"]}},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(
        Text, ForeignKey("users.username", ondelete="CASCADE")
    )
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("role.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

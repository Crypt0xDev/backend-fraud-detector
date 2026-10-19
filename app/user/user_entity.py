from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.user.user_schema import ACTIVE
from config.database import BaseModel
from utils.helpers import utcnow


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

    username = Column(Text, primary_key=True)
    password_hash = Column(Text, nullable=False)
    # Acceso total al sistema
    root = Column(Boolean, nullable=False, default=False, server_default="false")

    state = Column(Text, nullable=False, server_default=ACTIVE)
    # Sube al cambiar la contraseña; los tokens con otro número ya no sirven
    token_version = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )
    updated_at = Column(DateTime(timezone=True), default=None)

    roles = relationship("Role", secondary="user_role", order_by="Role.name")
    batches = relationship(
        "Batch",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    predictions = relationship(
        "PredictionRecord",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class UserRole(BaseModel):
    """Los roles que tiene cada usuario"""

    __tablename__ = "user_role"
    __table_args__ = (
        UniqueConstraint("username", "role_id", name="uq_user_role"),
        {"info": {"upgrades": ["ALTER TABLE user_role ENABLE ROW LEVEL SECURITY"]}},
    )

    id = Column(Integer, primary_key=True)
    username = Column(
        Text, ForeignKey("users.username", ondelete="CASCADE"), nullable=False
    )
    role_id = Column(Integer, ForeignKey("role.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )

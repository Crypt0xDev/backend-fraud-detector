from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from config.database import BaseModel
from app.role.role_schema import ROLE_ACTIVE, ROLE_DELETED
from utils.helpers import utcnow

if TYPE_CHECKING:
    from app.module.module_entity import ModulePermission

class Role(BaseModel):
    """
    Grupo de permisos que el root le da a los usuarios.
    """
    __tablename__ = "role"
    __table_args__ = (
        CheckConstraint(f"state IN ('{ROLE_ACTIVE}', '{ROLE_DELETED}')", name="role_state_check"),
        {
            "info": {
                "upgrades": [
                    f"ALTER TABLE role ADD COLUMN IF NOT EXISTS state TEXT NOT NULL DEFAULT '{ROLE_ACTIVE}'",
                    "ALTER TABLE role ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ",
                    "ALTER TABLE role DROP CONSTRAINT IF EXISTS role_state_check",
                    f"ALTER TABLE role ADD CONSTRAINT role_state_check CHECK (state IN ('{ROLE_ACTIVE}', '{ROLE_DELETED}'))",
                    "ALTER TABLE role ENABLE ROW LEVEL SECURITY",
                    # El nombre solo es único entre los roles no eliminados
                    f"CREATE UNIQUE INDEX IF NOT EXISTS role_name_active ON role (name) WHERE state <> '{ROLE_DELETED}'",
                    "ALTER TABLE role DROP CONSTRAINT IF EXISTS role_name_key",
                ]
            }
        },
    )

    # Columnas
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(Text, nullable=False, default=ROLE_ACTIVE, server_default=ROLE_ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relaciones
    role_permissions: Mapped[list["RolePermission"]] = relationship(back_populates="role", cascade="all, delete-orphan")


# Un rol eliminado deja libre su nombre para crear otro igual
Index(
    "role_name_active",
    Role.name,
    unique=True,
    postgresql_where=Role.state != ROLE_DELETED,
    sqlite_where=Role.state != ROLE_DELETED,
)


class RolePermission(BaseModel):
    """
    Los permisos que tiene cada rol.
    """
    __tablename__ = "role_permission"
    __table_args__ = (
        UniqueConstraint("role_id", "module_permission_id", name="uq_role_module_permission"),
        {"info": {"upgrades": ["ALTER TABLE role_permission ENABLE ROW LEVEL SECURITY"]}},
    )

    # Columnas
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("role.id", ondelete="CASCADE"), nullable=False)
    module_permission_id: Mapped[int] = mapped_column(Integer, ForeignKey("module_permission.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    # Relaciones
    role: Mapped[Role] = relationship(back_populates="role_permissions")
    module_permission: Mapped["ModulePermission"] = relationship()

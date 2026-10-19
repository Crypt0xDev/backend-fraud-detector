from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import BaseModel
from utils.helpers import utcnow

if TYPE_CHECKING:
    from app.module.module_entity import ModulePermission


class Role(BaseModel):
    """Grupo de permisos que el root le da a los usuarios"""

    __tablename__ = "role"
    __table_args__ = (
        {"info": {"upgrades": ["ALTER TABLE role ENABLE ROW LEVEL SECURITY"]}},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True)
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relaciones
    role_permissions: Mapped[list["RolePermission"]] = relationship(
        back_populates="role", cascade="all, delete-orphan"
    )


class RolePermission(BaseModel):
    """Los permisos que tiene cada rol"""

    __tablename__ = "role_permission"
    __table_args__ = (
        UniqueConstraint(
            "role_id", "module_permission_id", name="uq_role_module_permission"
        ),
        {
            "info": {
                "upgrades": ["ALTER TABLE role_permission ENABLE ROW LEVEL SECURITY"]
            }
        },
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("role.id", ondelete="CASCADE")
    )
    module_permission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("module_permission.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    # Relaciones
    role: Mapped[Role] = relationship(back_populates="role_permissions")
    module_permission: Mapped["ModulePermission"] = relationship()

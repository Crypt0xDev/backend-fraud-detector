from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import BaseModel
from utils.helpers import utcnow

if TYPE_CHECKING:
    from app.permission.permission_entity import Permission


class Module(BaseModel):
    """Sección del menú; el code no se cambia"""

    __tablename__ = "module"
    __table_args__ = (
        {"info": {"upgrades": ["ALTER TABLE module ENABLE ROW LEVEL SECURITY"]}},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(Text)
    is_parent: Mapped[bool] = mapped_column(Boolean, default=False)
    path: Mapped[str | None] = mapped_column(Text)
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("module.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    # Relaciones; al borrar un módulo se borran sus hijos
    parent: Mapped[Optional["Module"]] = relationship(
        back_populates="children", remote_side=[id]
    )
    children: Mapped[list["Module"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )
    module_permissions: Mapped[list["ModulePermission"]] = relationship(
        back_populates="module", cascade="all, delete-orphan"
    )


class ModulePermission(BaseModel):
    """Qué acciones se pueden hacer en cada módulo, por ejemplo lotes + eliminar"""

    __tablename__ = "module_permission"
    __table_args__ = (
        UniqueConstraint("module_id", "permission_id", name="uq_module_permission"),
        {
            "info": {
                "upgrades": ["ALTER TABLE module_permission ENABLE ROW LEVEL SECURITY"]
            }
        },
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    module_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("module.id", ondelete="CASCADE")
    )
    permission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("permission.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    # Relaciones
    module: Mapped[Module] = relationship(back_populates="module_permissions")
    permission: Mapped["Permission"] = relationship(back_populates="permission_modules")

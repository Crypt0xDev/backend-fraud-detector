from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import BaseModel
from utils.helpers import utcnow

if TYPE_CHECKING:
    from app.module.module_entity import ModulePermission


class Permission(BaseModel):
    """Acciones: ver, crear, editar y eliminar"""

    __tablename__ = "permission"
    __table_args__ = (
        {"info": {"upgrades": ["ALTER TABLE permission ENABLE ROW LEVEL SECURITY"]}},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    # Relaciones
    permission_modules: Mapped[list["ModulePermission"]] = relationship(
        back_populates="permission"
    )

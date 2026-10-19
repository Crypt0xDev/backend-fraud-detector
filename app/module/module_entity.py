from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from config.database import BaseModel
from utils.helpers import utcnow


class Module(BaseModel):
    """Sección del menú; el code no se cambia"""

    __tablename__ = "module"
    __table_args__ = (
        {"info": {"upgrades": ["ALTER TABLE module ENABLE ROW LEVEL SECURITY"]}},
    )

    id = Column(Integer, primary_key=True)
    code = Column(Text, nullable=False, unique=True)
    name = Column(Text, nullable=False)
    icon = Column(Text, nullable=True)
    is_parent = Column(Boolean, nullable=False, default=False)
    path = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("module.id"), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )

    # Relaciones
    children = relationship(
        "Module",
        backref="parent",
        remote_side=[id],
        cascade="all, delete-orphan",
        passive_deletes=True,
        single_parent=True,
    )
    module_permissions = relationship(
        "ModulePermission", back_populates="module", cascade="all, delete-orphan"
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

    id = Column(Integer, primary_key=True)
    module_id = Column(
        Integer, ForeignKey("module.id", ondelete="CASCADE"), nullable=False
    )
    permission_id = Column(
        Integer, ForeignKey("permission.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )

    # Relaciones
    module = relationship("Module", back_populates="module_permissions")
    permission = relationship("Permission", back_populates="permission_modules")

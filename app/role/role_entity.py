from sqlalchemy import (
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


class Role(BaseModel):
    """Grupo de permisos que el root le da a los usuarios"""

    __tablename__ = "role"
    __table_args__ = (
        {"info": {"upgrades": ["ALTER TABLE role ENABLE ROW LEVEL SECURITY"]}},
    )

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    description = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )
    updated_at = Column(DateTime(timezone=True), default=None)

    # Relaciones
    role_permissions = relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan"
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

    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey("role.id", ondelete="CASCADE"), nullable=False)
    module_permission_id = Column(
        Integer, ForeignKey("module_permission.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )

    # Relaciones
    role = relationship("Role", back_populates="role_permissions")
    module_permission = relationship("ModulePermission")

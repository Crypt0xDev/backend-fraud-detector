from sqlalchemy import Column, DateTime, Integer, Text, func
from sqlalchemy.orm import relationship

from config.database import BaseModel
from utils.helpers import utcnow


class Permission(BaseModel):
    """Acciones: ver, crear, editar y eliminar"""

    __tablename__ = "permission"
    __table_args__ = (
        {"info": {"upgrades": ["ALTER TABLE permission ENABLE ROW LEVEL SECURITY"]}},
    )

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )

    # Relaciones
    permission_modules = relationship("ModulePermission", back_populates="permission")

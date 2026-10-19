from sqlalchemy import (
    Column,
    DateTime,
    Double,
    ForeignKey,
    Index,
    Integer,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import relationship

from config.database import BaseModel
from utils.helpers import utcnow


class Batch(BaseModel):
    """CSV analizado; cada lote es de un usuario"""

    __tablename__ = "batches"
    __table_args__ = (
        {"info": {"upgrades": ["ALTER TABLE batches ENABLE ROW LEVEL SECURITY"]}},
    )

    id = Column(Uuid, primary_key=True)
    username = Column(
        Text, ForeignKey("users.username", ondelete="CASCADE"), nullable=False
    )
    file_name = Column(Text, nullable=False)
    total_rows = Column(Integer, nullable=False)
    flagged_rows = Column(Integer, nullable=False)
    threshold = Column(Double, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )

    # Relaciones
    user = relationship("User", back_populates="batches")


Index("batches_username_created_at", Batch.username, Batch.created_at.desc())

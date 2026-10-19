import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Double, ForeignKey, Index, Integer, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import BaseModel
from utils.helpers import utcnow

if TYPE_CHECKING:
    from app.user.user_entity import User


class Batch(BaseModel):
    """CSV analizado; cada lote es de un usuario"""

    __tablename__ = "batches"
    __table_args__ = (
        {"info": {"upgrades": ["ALTER TABLE batches ENABLE ROW LEVEL SECURITY"]}},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    username: Mapped[str] = mapped_column(
        Text, ForeignKey("users.username", ondelete="CASCADE")
    )
    file_name: Mapped[str] = mapped_column(Text)
    total_rows: Mapped[int] = mapped_column(Integer)
    flagged_rows: Mapped[int] = mapped_column(Integer)
    threshold: Mapped[float] = mapped_column(Double)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    # Relaciones
    user: Mapped["User"] = relationship(back_populates="batches")


Index("batches_username_created_at", Batch.username, Batch.created_at.desc())

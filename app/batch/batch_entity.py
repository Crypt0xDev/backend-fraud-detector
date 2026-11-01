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
    """
    CSV analizado.
    Regla: cada lote es de un usuario; al eliminar el usuario (borrado lógico) sus lotes se quedan.
    """
    __tablename__ = "batches"
    __table_args__ = (
        {
            "info": {
                "upgrades": [
                    "ALTER TABLE batches ENABLE ROW LEVEL SECURITY",
                    "ALTER TABLE batches ADD COLUMN IF NOT EXISTS model_version TEXT",
                ]
            }
        },
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    username: Mapped[str] = mapped_column(Text, ForeignKey("users.username", ondelete="CASCADE"), nullable=False)
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    flagged_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    threshold: Mapped[float] = mapped_column(Double, nullable=False)
    # Versión del modelo que analizó el CSV (None en los lotes de antes)
    model_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    # Relaciones
    user: Mapped["User"] = relationship(back_populates="batches")


Index("batches_username_created_at", Batch.username, Batch.created_at.desc())

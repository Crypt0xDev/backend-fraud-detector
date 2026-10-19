import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Double, ForeignKey, Index, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import BaseModel
from utils.helpers import utcnow

if TYPE_CHECKING:
    from app.user.user_entity import User


class PredictionRecord(BaseModel):
    """Transacción analizada con POST /predict"""

    __tablename__ = "predictions"
    __table_args__ = (
        {"info": {"upgrades": ["ALTER TABLE predictions ENABLE ROW LEVEL SECURITY"]}},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    # Se usa el nombre de la tabla para no importar nada del módulo user
    username: Mapped[str] = mapped_column(
        Text, ForeignKey("users.username", ondelete="CASCADE")
    )

    # Datos de la transacción
    type: Mapped[str] = mapped_column(Text)
    amount: Mapped[float] = mapped_column(Double)
    name_orig: Mapped[str | None] = mapped_column(Text)
    name_dest: Mapped[str | None] = mapped_column(Text)

    # Resultado del modelo
    fraud_probability: Mapped[float] = mapped_column(Double)
    is_fraud: Mapped[bool] = mapped_column(Boolean)
    threshold: Mapped[float] = mapped_column(Double)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    # Relaciones
    user: Mapped["User"] = relationship(back_populates="predictions")


Index(
    "predictions_username_created_at",
    PredictionRecord.username,
    PredictionRecord.created_at.desc(),
)

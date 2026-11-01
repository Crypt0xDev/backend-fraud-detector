import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, Double, ForeignKey, Index, Integer, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from config.database import BaseModel
from utils.helpers import utcnow

if TYPE_CHECKING:
    from app.user.user_entity import User


class PredictionRecord(BaseModel):
    """
    Transacción analizada con POST /predict.
    Regla: se usa el nombre de la tabla users para no importar nada del módulo user.
    """
    __tablename__ = "predictions"
    __table_args__ = (
        {
            "info": {
                "upgrades": [
                    "ALTER TABLE predictions ENABLE ROW LEVEL SECURITY",
                    "ALTER TABLE predictions ADD COLUMN IF NOT EXISTS model_version TEXT",
                ]
            }
        },
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    username: Mapped[str] = mapped_column(Text, ForeignKey("users.username", ondelete="CASCADE"), nullable=False)

    # Datos de la transacción
    type: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[float] = mapped_column(Double, nullable=False)
    name_orig: Mapped[str | None] = mapped_column(Text, nullable=True)
    name_dest: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Resultado del modelo
    fraud_probability: Mapped[float] = mapped_column(Double, nullable=False)
    is_fraud: Mapped[bool] = mapped_column(Boolean, nullable=False)
    threshold: Mapped[float] = mapped_column(Double, nullable=False)
    # Versión del modelo que dio el score (None en las predicciones de antes)
    model_version: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    # Relaciones
    user: Mapped["User"] = relationship(back_populates="predictions")


Index("predictions_username_created_at", PredictionRecord.username, PredictionRecord.created_at.desc())


class PredictionPolicy(BaseModel):
    """
    Umbrales de decisión ajustados desde la web.
    Regla: hay una sola fila (id 1); si no existe, se usan los del entrenamiento o FRAUD_THRESHOLD.
    """
    __tablename__ = "prediction_policy"
    __table_args__ = (
        {
            "info": {
                "upgrades": [
                    "ALTER TABLE prediction_policy ENABLE ROW LEVEL SECURITY",
                ]
            }
        },
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    medium: Mapped[float] = mapped_column(Double, nullable=False)
    high: Mapped[float] = mapped_column(Double, nullable=False)
    # Sin FK: el ajuste se conserva aunque se elimine al usuario
    updated_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

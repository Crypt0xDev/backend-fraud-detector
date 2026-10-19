from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Double,
    ForeignKey,
    Index,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import relationship

from config.database import BaseModel
from utils.helpers import utcnow


class PredictionRecord(BaseModel):
    """Transacción analizada con POST /predict"""

    __tablename__ = "predictions"
    __table_args__ = (
        {"info": {"upgrades": ["ALTER TABLE predictions ENABLE ROW LEVEL SECURITY"]}},
    )

    id = Column(Uuid, primary_key=True)
    # Se usa el nombre de la tabla para no importar nada del módulo user
    username = Column(
        Text, ForeignKey("users.username", ondelete="CASCADE"), nullable=False
    )

    # Datos de la transacción
    type = Column(Text, nullable=False)
    amount = Column(Double, nullable=False)
    name_orig = Column(Text, nullable=True)
    name_dest = Column(Text, nullable=True)

    # Resultado del modelo
    fraud_probability = Column(Double, nullable=False)
    is_fraud = Column(Boolean, nullable=False)
    threshold = Column(Double, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )

    # Relaciones
    user = relationship("User", back_populates="predictions")


Index(
    "predictions_username_created_at",
    PredictionRecord.username,
    PredictionRecord.created_at.desc(),
)

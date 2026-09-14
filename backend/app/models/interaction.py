import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ConfidenceLevel(str, enum.Enum):
    ENCONTRADA = "encontrada"        # información encontrada directamente en las fuentes
    INFERIDA = "inferida"            # inferida mínimamente a partir de los documentos
    NO_DISPONIBLE = "no_disponible"  # sin información suficiente


class Interaction(Base):
    """Registro de auditoría de cada consulta: quién preguntó, qué se recuperó, qué
    respondió el modelo y cuánto tardó. No almacena información personal más allá del
    identificador de usuario (opcional)."""

    __tablename__ = "interactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    confidence: Mapped[ConfidenceLevel] = mapped_column(Enum(ConfidenceLevel))
    retrieved_chunk_ids: Mapped[list] = mapped_column(JSON, default=list)
    model_used: Mapped[str] = mapped_column(String(120))
    response_time_ms: Mapped[int] = mapped_column(Integer)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

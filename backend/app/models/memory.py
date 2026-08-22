import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Float, Integer, String, DateTime, Text, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.app.core.database import Base


class MemoryType(StrEnum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    RELATIONSHIP = "relationship"
    EMOTIONAL = "emotional"


class EpisodicMemory(Base):
    __tablename__ = "episodic_memories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizens.id"), index=True
    )
    memory_type: Mapped[MemoryType] = mapped_column(Enum(MemoryType), default=MemoryType.EPISODIC)

    content: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(String(500), default="")

    importance: Mapped[float] = mapped_column(Float, default=0.5)
    emotional_valence: Mapped[float] = mapped_column(Float, default=0.0)

    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    involved_citizens: Mapped[list] = mapped_column(JSON, default=list)

    access_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sim_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    citizen: Mapped["Citizen"] = relationship(back_populates="memories")

    def __repr__(self) -> str:
        return f"<Memory {self.memory_type} importance={self.importance:.2f}>"


class EmotionalState(Base):
    __tablename__ = "emotional_states"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizens.id"), index=True
    )

    fear: Mapped[float] = mapped_column(Float, default=0.0)
    anger: Mapped[float] = mapped_column(Float, default=0.0)
    joy: Mapped[float] = mapped_column(Float, default=0.5)
    sadness: Mapped[float] = mapped_column(Float, default=0.0)
    trust: Mapped[float] = mapped_column(Float, default=0.5)
    surprise: Mapped[float] = mapped_column(Float, default=0.0)
    stress: Mapped[float] = mapped_column(Float, default=0.3)
    confidence: Mapped[float] = mapped_column(Float, default=0.6)

    trigger: Mapped[str | None] = mapped_column(String(500), nullable=True)

    sim_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    citizen: Mapped["Citizen"] = relationship(back_populates="emotional_states")


from backend.app.models.citizen import Citizen  # noqa: E402

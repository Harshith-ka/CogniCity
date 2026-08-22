import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Float, Integer, String, DateTime, Text, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.app.core.database import Base


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"


class EducationLevel(StrEnum):
    NONE = "none"
    HIGH_SCHOOL = "high_school"
    BACHELORS = "bachelors"
    MASTERS = "masters"
    DOCTORATE = "doctorate"


class TransportPreference(StrEnum):
    WALKING = "walking"
    CAR = "car"
    METRO = "metro"
    BUS = "bus"
    BIKE = "bike"


class Citizen(Base):
    __tablename__ = "citizens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[Gender] = mapped_column(Enum(Gender))
    education: Mapped[EducationLevel] = mapped_column(Enum(EducationLevel))
    occupation: Mapped[str] = mapped_column(String(100), default="unemployed")
    salary: Mapped[float] = mapped_column(Float, default=0.0)
    balance: Mapped[float] = mapped_column(Float, default=1000.0)

    personality_traits: Mapped[dict] = mapped_column(JSON, default=dict)
    goals: Mapped[list] = mapped_column(JSON, default=list)

    happiness: Mapped[float] = mapped_column(Float, default=0.7)
    stress: Mapped[float] = mapped_column(Float, default=0.3)
    health: Mapped[float] = mapped_column(Float, default=0.9)
    energy: Mapped[float] = mapped_column(Float, default=1.0)
    hunger: Mapped[float] = mapped_column(Float, default=0.0)
    social_need: Mapped[float] = mapped_column(Float, default=0.5)

    political_opinion: Mapped[float] = mapped_column(Float, default=0.5)
    transport_preference: Mapped[TransportPreference] = mapped_column(
        Enum(TransportPreference), default=TransportPreference.WALKING
    )

    home_location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True
    )
    workplace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True
    )
    current_location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True
    )

    current_activity: Mapped[str] = mapped_column(String(100), default="idle")
    schedule: Mapped[dict] = mapped_column(JSON, default=dict)

    is_alive: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    memories: Mapped[list["EpisodicMemory"]] = relationship(back_populates="citizen")
    emotional_states: Mapped[list["EmotionalState"]] = relationship(back_populates="citizen")
    employments: Mapped[list["Employment"]] = relationship(back_populates="citizen")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="citizen")

    home_location: Mapped["Location | None"] = relationship(foreign_keys=[home_location_id])
    workplace: Mapped["Location | None"] = relationship(foreign_keys=[workplace_id])
    current_location: Mapped["Location | None"] = relationship(foreign_keys=[current_location_id])

    def __repr__(self) -> str:
        return f"<Citizen {self.name} age={self.age} occupation={self.occupation}>"


from backend.app.models.memory import EpisodicMemory, EmotionalState  # noqa: E402
from backend.app.models.economy import Employment, Transaction  # noqa: E402
from backend.app.models.city import Location  # noqa: E402

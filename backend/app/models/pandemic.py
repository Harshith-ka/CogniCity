import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Float, Integer, String, DateTime, Text, Enum, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.core.database import Base


class HealthStatus(StrEnum):
    SUSCEPTIBLE = "susceptible"
    EXPOSED = "exposed"
    INFECTED = "infected"
    SYMPTOMATIC = "symptomatic"
    HOSPITALIZED = "hospitalized"
    RECOVERED = "recovered"
    DECEASED = "deceased"
    VACCINATED = "vaccinated"


class Pandemic(Base):
    __tablename__ = "pandemics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    pathogen: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")

    r0: Mapped[float] = mapped_column(Float, default=2.5)
    infection_rate: Mapped[float] = mapped_column(Float, default=0.05)
    recovery_rate: Mapped[float] = mapped_column(Float, default=0.02)
    mortality_rate: Mapped[float] = mapped_column(Float, default=0.01)
    incubation_ticks: Mapped[int] = mapped_column(Integer, default=20)
    symptom_onset_ticks: Mapped[int] = mapped_column(Integer, default=10)

    total_cases: Mapped[int] = mapped_column(Integer, default=0)
    active_cases: Mapped[int] = mapped_column(Integer, default=0)
    recovered: Mapped[int] = mapped_column(Integer, default=0)
    deaths: Mapped[int] = mapped_column(Integer, default=0)
    vaccinated: Mapped[int] = mapped_column(Integer, default=0)
    hospitalized: Mapped[int] = mapped_column(Integer, default=0)

    hospital_capacity: Mapped[int] = mapped_column(Integer, default=50)
    vaccination_available: Mapped[bool] = mapped_column(default=False)
    vaccination_rate: Mapped[float] = mapped_column(Float, default=0.0)
    lockdown_active: Mapped[bool] = mapped_column(default=False)
    mask_mandate: Mapped[bool] = mapped_column(default=False)

    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(default=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CitizenHealthRecord(Base):
    __tablename__ = "citizen_health_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizens.id"), index=True
    )
    pandemic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pandemics.id"), index=True
    )
    health_status: Mapped[HealthStatus] = mapped_column(
        Enum(HealthStatus), default=HealthStatus.SUSCEPTIBLE
    )
    infected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recovered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ticks_since_infection: Mapped[int] = mapped_column(Integer, default=0)
    is_quarantined: Mapped[bool] = mapped_column(default=False)
    is_vaccinated: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

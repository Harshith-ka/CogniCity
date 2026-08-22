"""Phase 5 models: Crime & Public Safety."""

import uuid
from datetime import datetime

from sqlalchemy import Float, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.core.database import Base


class CrimeRecord(Base):
    __tablename__ = "crime_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crime_type: Mapped[str] = mapped_column(String(50))  # theft, assault, fraud, vandalism, burglary, robbery, drug_offense
    severity: Mapped[str] = mapped_column(String(20))  # minor, moderate, serious, severe
    district_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("districts.id"), nullable=True)

    perpetrator_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("citizens.id"), nullable=True)
    victim_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("citizens.id"), nullable=True)

    is_solved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_reported: Mapped[bool] = mapped_column(Boolean, default=True)
    response_time_ticks: Mapped[int] = mapped_column(Integer, default=0)
    economic_damage: Mapped[float] = mapped_column(Float, default=0.0)

    description: Mapped[str] = mapped_column(Text, default="")
    sim_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PoliceUnit(Base):
    __tablename__ = "police_units"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    district_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("districts.id"), nullable=True)
    officers: Mapped[int] = mapped_column(Integer, default=10)
    capacity: Mapped[int] = mapped_column(Integer, default=20)
    effectiveness: Mapped[float] = mapped_column(Float, default=0.7)
    active_cases: Mapped[int] = mapped_column(Integer, default=0)
    cases_solved: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

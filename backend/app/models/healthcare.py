"""Phase 5 models: Healthcare & Wellness."""

import uuid
from datetime import datetime

from sqlalchemy import Float, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.core.database import Base


class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    hospital_type: Mapped[str] = mapped_column(String(50))  # general, emergency, psychiatric, clinic
    district_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("districts.id"), nullable=True)
    # Exact sim-world placement — nullable because pre-existing/auto-generated hospitals
    # only ever had a district. A manually placed one (via Build Mode) always sets these,
    # so distance/coverage math can use the real point instead of the district centroid.
    x: Mapped[float | None] = mapped_column(Float, nullable=True)
    y: Mapped[float | None] = mapped_column(Float, nullable=True)

    total_beds: Mapped[int] = mapped_column(Integer, default=100)
    occupied_beds: Mapped[int] = mapped_column(Integer, default=0)
    icu_beds: Mapped[int] = mapped_column(Integer, default=10)
    icu_occupied: Mapped[int] = mapped_column(Integer, default=0)

    staff_count: Mapped[int] = mapped_column(Integer, default=50)
    quality_rating: Mapped[float] = mapped_column(Float, default=0.7)
    funding: Mapped[float] = mapped_column(Float, default=500000.0)
    is_operational: Mapped[bool] = mapped_column(Boolean, default=True)


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    citizen_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("citizens.id"))
    hospital_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=True)

    condition: Mapped[str] = mapped_column(String(100))  # flu, injury, stress_disorder, chronic_pain, depression, anxiety, food_poisoning
    condition_type: Mapped[str] = mapped_column(String(50))  # physical, mental, chronic, acute
    severity: Mapped[float] = mapped_column(Float, default=0.5)

    is_hospitalized: Mapped[bool] = mapped_column(Boolean, default=False)
    is_treated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    treatment_cost: Mapped[float] = mapped_column(Float, default=0.0)
    treatment_ticks: Mapped[int] = mapped_column(Integer, default=0)
    ticks_remaining: Mapped[int] = mapped_column(Integer, default=0)

    diagnosis: Mapped[str] = mapped_column(Text, default="")
    sim_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

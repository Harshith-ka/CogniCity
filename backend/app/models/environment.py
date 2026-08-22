"""Phase 6 models: Environment & Sustainability."""

import uuid
from datetime import datetime

from sqlalchemy import Float, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.core.database import Base


class EnvironmentState(Base):
    __tablename__ = "environment_states"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    air_quality_index: Mapped[int] = mapped_column(Integer, default=50)
    water_quality: Mapped[float] = mapped_column(Float, default=0.8)
    noise_level_db: Mapped[float] = mapped_column(Float, default=55.0)
    green_coverage_pct: Mapped[float] = mapped_column(Float, default=0.25)
    carbon_emissions_tons: Mapped[float] = mapped_column(Float, default=500.0)
    recycling_rate: Mapped[float] = mapped_column(Float, default=0.3)
    renewable_energy_pct: Mapped[float] = mapped_column(Float, default=0.2)
    waste_tons: Mapped[float] = mapped_column(Float, default=100.0)

    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    sim_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GreenInitiative(Base):
    __tablename__ = "green_initiatives"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    initiative_type: Mapped[str] = mapped_column(String(50))  # solar_panel, wind_farm, recycling_program, tree_planting, ev_charging, water_treatment
    district_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("districts.id"), nullable=True)

    cost: Mapped[float] = mapped_column(Float, default=50000.0)
    impact_carbon: Mapped[float] = mapped_column(Float, default=-10.0)
    impact_air_quality: Mapped[int] = mapped_column(Integer, default=-5)
    impact_renewable_pct: Mapped[float] = mapped_column(Float, default=0.02)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sim_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

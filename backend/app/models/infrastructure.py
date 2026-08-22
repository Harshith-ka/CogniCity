"""Phase 6 models: Infrastructure & Utilities."""

import uuid
from datetime import datetime

from sqlalchemy import Float, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.core.database import Base


class UtilityGrid(Base):
    __tablename__ = "utility_grids"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    utility_type: Mapped[str] = mapped_column(String(50))  # power, water, internet, gas
    district_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("districts.id"), nullable=True)

    capacity: Mapped[float] = mapped_column(Float, default=1000.0)
    current_load: Mapped[float] = mapped_column(Float, default=500.0)
    reliability: Mapped[float] = mapped_column(Float, default=0.95)
    coverage_pct: Mapped[float] = mapped_column(Float, default=0.9)
    price_per_unit: Mapped[float] = mapped_column(Float, default=0.1)
    health: Mapped[float] = mapped_column(Float, default=0.85)
    last_maintenance: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_operational: Mapped[bool] = mapped_column(Boolean, default=True)


class InfraProject(Base):
    __tablename__ = "infra_projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    # road_repair, grid_upgrade, pipe_replacement, fiber_install, bridge_build,
    # hospital_build, school_build, colony_build, road_build
    project_type: Mapped[str] = mapped_column(String(50))
    district_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("districts.id"), nullable=True)

    # Exact sim-world placement, set when a project is manually triggered at a
    # location. road_build additionally uses target_x/target_y as its far endpoint.
    x: Mapped[float | None] = mapped_column(Float, nullable=True)
    y: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_y: Mapped[float | None] = mapped_column(Float, nullable=True)

    budget: Mapped[float] = mapped_column(Float, default=100000.0)
    spent: Mapped[float] = mapped_column(Float, default=0.0)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    impact_reliability: Mapped[float] = mapped_column(Float, default=0.1)
    impact_capacity: Mapped[float] = mapped_column(Float, default=0.0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    sim_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

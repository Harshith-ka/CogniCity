"""Phase 6 models: Demographics & Population."""

import uuid
from datetime import datetime

from sqlalchemy import Float, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.core.database import Base


class LifeEvent(Base):
    __tablename__ = "life_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    citizen_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("citizens.id"))
    event_type: Mapped[str] = mapped_column(String(50))  # birth, death, marriage, divorce, immigration, emigration, retirement, promotion
    description: Mapped[str] = mapped_column(String(500), default="")
    related_citizen_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("citizens.id"), nullable=True)
    sim_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PopulationSnapshot(Base):
    __tablename__ = "population_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tick: Mapped[int] = mapped_column(Integer)
    total_population: Mapped[int] = mapped_column(Integer, default=0)
    births: Mapped[int] = mapped_column(Integer, default=0)
    deaths: Mapped[int] = mapped_column(Integer, default=0)
    immigrants: Mapped[int] = mapped_column(Integer, default=0)
    emigrants: Mapped[int] = mapped_column(Integer, default=0)
    avg_age: Mapped[float] = mapped_column(Float, default=35.0)
    dependency_ratio: Mapped[float] = mapped_column(Float, default=0.5)
    growth_rate: Mapped[float] = mapped_column(Float, default=0.0)
    sim_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

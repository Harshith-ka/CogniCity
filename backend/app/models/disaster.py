import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Float, Integer, String, DateTime, Text, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.app.core.database import Base


class DisasterType(StrEnum):
    EARTHQUAKE = "earthquake"
    FLOOD = "flood"
    CYCLONE = "cyclone"
    FIRE = "fire"
    TORNADO = "tornado"
    TSUNAMI = "tsunami"
    LANDSLIDE = "landslide"


class DisasterPhase(StrEnum):
    ONSET = "onset"
    PEAK = "peak"
    DECLINING = "declining"
    RECOVERY = "recovery"
    RESOLVED = "resolved"


class Disaster(Base):
    __tablename__ = "disasters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    disaster_type: Mapped[DisasterType] = mapped_column(Enum(DisasterType))
    phase: Mapped[DisasterPhase] = mapped_column(Enum(DisasterPhase), default=DisasterPhase.ONSET)

    epicenter_x: Mapped[float] = mapped_column(Float, default=0.0)
    epicenter_y: Mapped[float] = mapped_column(Float, default=0.0)
    radius: Mapped[float] = mapped_column(Float, default=500.0)
    intensity: Mapped[float] = mapped_column(Float, default=0.5)
    max_intensity: Mapped[float] = mapped_column(Float, default=0.5)

    casualties: Mapped[int] = mapped_column(Integer, default=0)
    injuries: Mapped[int] = mapped_column(Integer, default=0)
    buildings_damaged: Mapped[int] = mapped_column(Integer, default=0)
    buildings_destroyed: Mapped[int] = mapped_column(Integer, default=0)
    evacuated: Mapped[int] = mapped_column(Integer, default=0)
    economic_damage: Mapped[float] = mapped_column(Float, default=0.0)

    spread_rate: Mapped[float] = mapped_column(Float, default=0.0)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)

    duration_ticks: Mapped[int] = mapped_column(Integer, default=100)
    elapsed_ticks: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(default=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EvacuationZone(Base):
    __tablename__ = "evacuation_zones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disaster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("disasters.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    center_x: Mapped[float] = mapped_column(Float)
    center_y: Mapped[float] = mapped_column(Float)
    radius: Mapped[float] = mapped_column(Float)
    evacuees: Mapped[int] = mapped_column(Integer, default=0)
    capacity: Mapped[int] = mapped_column(Integer, default=500)
    is_active: Mapped[bool] = mapped_column(default=True)

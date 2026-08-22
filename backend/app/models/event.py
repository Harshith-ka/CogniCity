import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Float, Integer, String, DateTime, Text, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.core.database import Base


class EventCategory(StrEnum):
    NATURAL_DISASTER = "natural_disaster"
    HEALTH = "health"
    ECONOMIC = "economic"
    INFRASTRUCTURE = "infrastructure"
    SOCIAL = "social"
    POLITICAL = "political"


class EventSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CityEvent(Base):
    __tablename__ = "city_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[EventCategory] = mapped_column(Enum(EventCategory))
    severity: Mapped[EventSeverity] = mapped_column(Enum(EventSeverity))
    description: Mapped[str] = mapped_column(Text)

    affected_area_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    affected_area_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    affected_radius: Mapped[float] = mapped_column(Float, default=100.0)

    impact: Mapped[dict] = mapped_column(JSON, default=dict)
    duration_ticks: Mapped[int] = mapped_column(Integer, default=60)
    remaining_ticks: Mapped[int] = mapped_column(Integer, default=60)

    is_active: Mapped[bool] = mapped_column(default=True)

    sim_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    sim_ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

"""Phase 6 models: Culture & Entertainment."""

import uuid
from datetime import datetime

from sqlalchemy import Float, Integer, String, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.core.database import Base


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    venue_type: Mapped[str] = mapped_column(String(50))  # theater, stadium, restaurant, bar, museum, gallery, park, club
    district_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("districts.id"), nullable=True)

    capacity: Mapped[int] = mapped_column(Integer, default=100)
    popularity: Mapped[float] = mapped_column(Float, default=0.5)
    quality: Mapped[float] = mapped_column(Float, default=0.6)
    ticket_price: Mapped[float] = mapped_column(Float, default=20.0)
    daily_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    total_visitors: Mapped[int] = mapped_column(Integer, default=0)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)


class CityFestival(Base):
    __tablename__ = "city_festivals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    event_type: Mapped[str] = mapped_column(String(50))  # concert, festival, sports, exhibition, parade, food_fair
    venue_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=True)
    district_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("districts.id"), nullable=True)

    description: Mapped[str] = mapped_column(Text, default="")
    attendees: Mapped[int] = mapped_column(Integer, default=0)
    max_attendees: Mapped[int] = mapped_column(Integer, default=500)
    happiness_boost: Mapped[float] = mapped_column(Float, default=0.05)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    duration_ticks: Mapped[int] = mapped_column(Integer, default=10)
    ticks_remaining: Mapped[int] = mapped_column(Integer, default=0)

    tags: Mapped[list] = mapped_column(JSON, default=list)
    sim_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sim_ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

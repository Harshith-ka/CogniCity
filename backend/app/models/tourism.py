"""Phase 6 models: Tourism & Visitors."""

import uuid
from datetime import datetime

from sqlalchemy import Float, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.core.database import Base


class Hotel(Base):
    __tablename__ = "hotels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    hotel_class: Mapped[int] = mapped_column(Integer, default=3)  # 1-5 stars
    district_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("districts.id"), nullable=True)

    total_rooms: Mapped[int] = mapped_column(Integer, default=50)
    occupied_rooms: Mapped[int] = mapped_column(Integer, default=0)
    price_per_night: Mapped[float] = mapped_column(Float, default=100.0)
    rating: Mapped[float] = mapped_column(Float, default=4.0)
    amenities: Mapped[list] = mapped_column(JSON, default=list)
    daily_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    total_guests: Mapped[int] = mapped_column(Integer, default=0)


class TouristAttraction(Base):
    __tablename__ = "tourist_attractions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    attraction_type: Mapped[str] = mapped_column(String(50))  # landmark, museum, park, monument, beach, theme_park
    district_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("districts.id"), nullable=True)

    popularity: Mapped[float] = mapped_column(Float, default=0.5)
    ticket_price: Mapped[float] = mapped_column(Float, default=15.0)
    daily_visitors: Mapped[int] = mapped_column(Integer, default=0)
    total_visitors: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=4.0)
    capacity: Mapped[int] = mapped_column(Integer, default=200)


class TouristVisitor(Base):
    __tablename__ = "tourist_visitors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    origin_country: Mapped[str] = mapped_column(String(100), default="Domestic")
    hotel_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("hotels.id"), nullable=True)

    budget: Mapped[float] = mapped_column(Float, default=500.0)
    spent: Mapped[float] = mapped_column(Float, default=0.0)
    satisfaction: Mapped[float] = mapped_column(Float, default=0.7)
    stay_duration_ticks: Mapped[int] = mapped_column(Integer, default=20)
    ticks_remaining: Mapped[int] = mapped_column(Integer, default=20)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    arrived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

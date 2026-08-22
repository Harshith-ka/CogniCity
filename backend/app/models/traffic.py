import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Float, Integer, String, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.core.database import Base


class VehicleType(StrEnum):
    PEDESTRIAN = "pedestrian"
    CAR = "car"
    BUS = "bus"
    METRO = "metro"
    BIKE = "bike"
    EMERGENCY = "emergency"
    TRUCK = "truck"


class RoadSegment(Base):
    __tablename__ = "road_segments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))

    start_x: Mapped[float] = mapped_column(Float)
    start_y: Mapped[float] = mapped_column(Float)
    end_x: Mapped[float] = mapped_column(Float)
    end_y: Mapped[float] = mapped_column(Float)

    length_m: Mapped[float] = mapped_column(Float)
    speed_limit: Mapped[float] = mapped_column(Float, default=50.0)
    lanes: Mapped[int] = mapped_column(Integer, default=2)
    capacity: Mapped[int] = mapped_column(Integer, default=100)
    current_vehicles: Mapped[int] = mapped_column(Integer, default=0)

    congestion_level: Mapped[float] = mapped_column(Float, default=0.0)
    is_blocked: Mapped[bool] = mapped_column(default=False)

    connected_segments: Mapped[list] = mapped_column(JSON, default=list)


class TransitRoute(Base):
    __tablename__ = "transit_routes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    route_type: Mapped[VehicleType] = mapped_column(Enum(VehicleType))

    stops: Mapped[list] = mapped_column(JSON, default=list)
    frequency_minutes: Mapped[int] = mapped_column(Integer, default=10)
    fare: Mapped[float] = mapped_column(Float, default=2.50)
    capacity_per_vehicle: Mapped[int] = mapped_column(Integer, default=100)

    is_active: Mapped[bool] = mapped_column(default=True)


class TripRecord(Base):
    __tablename__ = "trip_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizens.id"), index=True
    )
    vehicle_type: Mapped[VehicleType] = mapped_column(Enum(VehicleType))

    origin_x: Mapped[float] = mapped_column(Float)
    origin_y: Mapped[float] = mapped_column(Float)
    dest_x: Mapped[float] = mapped_column(Float)
    dest_y: Mapped[float] = mapped_column(Float)

    distance_m: Mapped[float] = mapped_column(Float)
    duration_minutes: Mapped[float] = mapped_column(Float)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    congestion_experienced: Mapped[float] = mapped_column(Float, default=0.0)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

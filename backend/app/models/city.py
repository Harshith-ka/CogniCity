import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Float, Integer, String, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.app.core.database import Base


class LocationType(StrEnum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    GOVERNMENT = "government"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    PARK = "park"
    TRANSPORT_HUB = "transport_hub"
    RELIGIOUS = "religious"


class BuildingType(StrEnum):
    HOUSE = "house"
    APARTMENT = "apartment"
    OFFICE = "office"
    SHOP = "shop"
    HOSPITAL = "hospital"
    SCHOOL = "school"
    UNIVERSITY = "university"
    RESTAURANT = "restaurant"
    GYM = "gym"
    PARK = "park"
    METRO_STATION = "metro_station"
    BUS_STOP = "bus_stop"
    FACTORY = "factory"
    GOVERNMENT_BUILDING = "government_building"
    POLICE_STATION = "police_station"
    FIRE_STATION = "fire_station"


class District(Base):
    __tablename__ = "districts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(500), default="")
    population: Mapped[int] = mapped_column(Integer, default=0)
    safety_index: Mapped[float] = mapped_column(Float, default=0.8)
    wealth_index: Mapped[float] = mapped_column(Float, default=0.5)
    pollution_index: Mapped[float] = mapped_column(Float, default=0.2)

    center_x: Mapped[float] = mapped_column(Float, default=0.0)
    center_y: Mapped[float] = mapped_column(Float, default=0.0)
    radius: Mapped[float] = mapped_column(Float, default=500.0)

    locations: Mapped[list["Location"]] = relationship(back_populates="district")


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    location_type: Mapped[LocationType] = mapped_column(Enum(LocationType))
    district_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("districts.id"), nullable=True
    )

    x: Mapped[float] = mapped_column(Float, default=0.0)
    y: Mapped[float] = mapped_column(Float, default=0.0)

    capacity: Mapped[int] = mapped_column(Integer, default=50)
    current_occupancy: Mapped[int] = mapped_column(Integer, default=0)

    properties: Mapped[dict] = mapped_column(JSON, default=dict)

    district: Mapped["District | None"] = relationship(back_populates="locations")
    buildings: Mapped[list["Building"]] = relationship(back_populates="location")


class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    building_type: Mapped[BuildingType] = mapped_column(Enum(BuildingType))
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id")
    )

    floors: Mapped[int] = mapped_column(Integer, default=1)
    condition: Mapped[float] = mapped_column(Float, default=1.0)
    rent_cost: Mapped[float] = mapped_column(Float, default=500.0)
    value: Mapped[float] = mapped_column(Float, default=100000.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    location: Mapped["Location"] = relationship(back_populates="buildings")

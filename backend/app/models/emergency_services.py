"""Fire & emergency response infrastructure — mirrors PoliceUnit's shape (crime.py)
since there was no equivalent model before Build Mode needed one to place a real,
persistent fire station rather than a cosmetic 3D object."""

import uuid

from sqlalchemy import Float, Integer, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


class FireStation(Base):
    __tablename__ = "fire_stations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    district_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("districts.id"), nullable=True)
    x: Mapped[float | None] = mapped_column(Float, nullable=True)
    y: Mapped[float | None] = mapped_column(Float, nullable=True)

    firefighters: Mapped[int] = mapped_column(Integer, default=15)
    response_capacity: Mapped[int] = mapped_column(Integer, default=20)  # simultaneous incidents it can crew
    effectiveness: Mapped[float] = mapped_column(Float, default=0.75)
    active_incidents: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

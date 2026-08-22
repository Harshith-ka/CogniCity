"""Phase 5 models: Weather & Environment."""

import uuid
from datetime import datetime

from sqlalchemy import Float, Integer, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.core.database import Base


class WeatherState(Base):
    __tablename__ = "weather_states"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    condition: Mapped[str] = mapped_column(String(50))  # clear, cloudy, rain, storm, snow, fog, heatwave, cold_snap
    temperature_c: Mapped[float] = mapped_column(Float, default=22.0)
    humidity: Mapped[float] = mapped_column(Float, default=0.5)
    wind_speed_kmh: Mapped[float] = mapped_column(Float, default=10.0)
    visibility_km: Mapped[float] = mapped_column(Float, default=10.0)
    air_quality_index: Mapped[int] = mapped_column(Integer, default=50)
    uv_index: Mapped[float] = mapped_column(Float, default=5.0)
    precipitation_mm: Mapped[float] = mapped_column(Float, default=0.0)

    season: Mapped[str] = mapped_column(String(20), default="summer")
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    sim_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    happiness_modifier: Mapped[float] = mapped_column(Float, default=0.0)
    health_modifier: Mapped[float] = mapped_column(Float, default=0.0)
    traffic_modifier: Mapped[float] = mapped_column(Float, default=1.0)
    crime_modifier: Mapped[float] = mapped_column(Float, default=1.0)

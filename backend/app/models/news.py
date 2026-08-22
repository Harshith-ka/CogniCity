"""Phase 5 models: News & Media."""

import uuid
from datetime import datetime

from sqlalchemy import Float, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.core.database import Base


class NewsOutlet(Base):
    __tablename__ = "news_outlets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    outlet_type: Mapped[str] = mapped_column(String(50))  # newspaper, tv, radio, online, blog
    political_bias: Mapped[float] = mapped_column(Float, default=0.0)  # -1.0 left to 1.0 right
    credibility: Mapped[float] = mapped_column(Float, default=0.7)
    reach: Mapped[float] = mapped_column(Float, default=0.5)  # fraction of population
    sensationalism: Mapped[float] = mapped_column(Float, default=0.3)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outlet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("news_outlets.id"))
    headline: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(50))  # crime, politics, economy, disaster, health, sports, community, weather
    sentiment: Mapped[float] = mapped_column(Float, default=0.0)  # -1 to 1

    source_event_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    views: Mapped[int] = mapped_column(Integer, default=0)
    impact_on_happiness: Mapped[float] = mapped_column(Float, default=0.0)
    impact_on_stress: Mapped[float] = mapped_column(Float, default=0.0)
    impact_on_opinion: Mapped[float] = mapped_column(Float, default=0.0)

    tags: Mapped[list] = mapped_column(JSON, default=list)
    is_breaking: Mapped[bool] = mapped_column(Boolean, default=False)
    sim_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Float, Integer, String, DateTime, Text, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.core.database import Base


class TopicCategory(StrEnum):
    NEWS = "news"
    ENTERTAINMENT = "entertainment"
    POLITICS = "politics"
    ECONOMY = "economy"
    HEALTH = "health"
    DISASTER = "disaster"
    SPORTS = "sports"
    COMMUNITY = "community"


class TrendingTopic(Base):
    __tablename__ = "trending_topics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hashtag: Mapped[str] = mapped_column(String(100), index=True)
    topic: Mapped[str] = mapped_column(String(300))
    category: Mapped[TopicCategory] = mapped_column(Enum(TopicCategory))

    mention_count: Mapped[int] = mapped_column(Integer, default=1)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    virality: Mapped[float] = mapped_column(Float, default=0.0)
    peak_mentions: Mapped[int] = mapped_column(Integer, default=1)

    is_misinformation: Mapped[bool] = mapped_column(default=False)
    is_trending: Mapped[bool] = mapped_column(default=True)

    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OpinionShift(Base):
    __tablename__ = "opinion_shifts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizens.id"), index=True
    )
    topic: Mapped[str] = mapped_column(String(200))
    old_opinion: Mapped[float] = mapped_column(Float)
    new_opinion: Mapped[float] = mapped_column(Float)
    influence_source: Mapped[str] = mapped_column(String(200))
    sim_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

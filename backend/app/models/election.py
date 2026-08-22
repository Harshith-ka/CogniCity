import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Float, Integer, String, DateTime, Text, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.app.core.database import Base


class ElectionPhase(StrEnum):
    ANNOUNCEMENT = "announcement"
    CAMPAIGNING = "campaigning"
    DEBATE = "debate"
    VOTING = "voting"
    COUNTING = "counting"
    COMPLETED = "completed"


class Election(Base):
    __tablename__ = "elections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    phase: Mapped[ElectionPhase] = mapped_column(Enum(ElectionPhase), default=ElectionPhase.ANNOUNCEMENT)

    total_voters: Mapped[int] = mapped_column(Integer, default=0)
    votes_cast: Mapped[int] = mapped_column(Integer, default=0)
    turnout_rate: Mapped[float] = mapped_column(Float, default=0.0)

    winner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    winner_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    results: Mapped[dict] = mapped_column(JSON, default=dict)

    phase_ticks_remaining: Mapped[int] = mapped_column(Integer, default=50)
    total_ticks: Mapped[int] = mapped_column(Integer, default=300)
    elapsed_ticks: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(default=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    candidates: Mapped[list["Candidate"]] = relationship(back_populates="election")


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    election_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("elections.id"), index=True
    )
    citizen_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizens.id"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(200))
    party: Mapped[str] = mapped_column(String(100), default="Independent")
    platform: Mapped[dict] = mapped_column(JSON, default=dict)
    slogan: Mapped[str] = mapped_column(String(300), default="")

    popularity: Mapped[float] = mapped_column(Float, default=0.3)
    campaign_funds: Mapped[float] = mapped_column(Float, default=10000.0)
    votes: Mapped[int] = mapped_column(Integer, default=0)
    vote_share: Mapped[float] = mapped_column(Float, default=0.0)

    is_winner: Mapped[bool] = mapped_column(default=False)

    election: Mapped["Election"] = relationship(back_populates="candidates")

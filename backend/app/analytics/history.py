"""
Metrics History: Stores time-series snapshots of city metrics for charting.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Float, Integer, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.core.database import Base


class MetricsSnapshot(Base):
    __tablename__ = "metrics_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tick: Mapped[int] = mapped_column(Integer, index=True)
    sim_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    population: Mapped[int] = mapped_column(Integer, default=0)
    employed: Mapped[int] = mapped_column(Integer, default=0)
    unemployment_rate: Mapped[float] = mapped_column(Float, default=0.0)

    avg_happiness: Mapped[float] = mapped_column(Float, default=0.0)
    avg_health: Mapped[float] = mapped_column(Float, default=0.0)
    avg_stress: Mapped[float] = mapped_column(Float, default=0.0)

    total_gdp: Mapped[float] = mapped_column(Float, default=0.0)
    avg_income: Mapped[float] = mapped_column(Float, default=0.0)

    active_events: Mapped[int] = mapped_column(Integer, default=0)
    conversations: Mapped[int] = mapped_column(Integer, default=0)
    trips: Mapped[int] = mapped_column(Integer, default=0)
    avg_congestion: Mapped[float] = mapped_column(Float, default=0.0)

    extra: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MetricsHistoryTracker:
    """Records periodic snapshots of city metrics."""

    def __init__(self, db):
        self.db = db

    async def record_snapshot(
        self,
        tick: int,
        sim_time: datetime,
        metrics: dict,
    ) -> MetricsSnapshot:
        snapshot = MetricsSnapshot(
            tick=tick,
            sim_time=sim_time,
            population=metrics.get("population", 0),
            employed=metrics.get("employed", 0),
            unemployment_rate=metrics.get("unemployment_rate", 0.0),
            avg_happiness=metrics.get("avg_happiness", 0.0),
            avg_health=metrics.get("avg_health", 0.0),
            avg_stress=metrics.get("avg_stress", 0.0),
            total_gdp=metrics.get("total_gdp", 0.0),
            avg_income=metrics.get("avg_income", 0.0),
            active_events=metrics.get("active_events", 0),
            conversations=metrics.get("conversations", 0),
            trips=metrics.get("trips", 0),
            avg_congestion=metrics.get("avg_congestion", 0.0),
        )
        self.db.add(snapshot)
        await self.db.flush()
        return snapshot

    async def get_history(self, limit: int = 100) -> list[dict]:
        from sqlalchemy import select, desc

        result = await self.db.execute(
            select(MetricsSnapshot)
            .order_by(desc(MetricsSnapshot.tick))
            .limit(limit)
        )
        snapshots = list(result.scalars().all())
        snapshots.reverse()

        return [
            {
                "tick": s.tick,
                "sim_time": s.sim_time.isoformat(),
                "population": s.population,
                "unemployment_rate": s.unemployment_rate,
                "avg_happiness": s.avg_happiness,
                "avg_health": s.avg_health,
                "avg_stress": s.avg_stress,
                "total_gdp": s.total_gdp,
                "avg_congestion": s.avg_congestion,
            }
            for s in snapshots
        ]

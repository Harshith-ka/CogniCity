"""Usage metering — Phase 2 of the multi-tenant platform plan.

The foundation every pricing model reads from: subscriptions enforce quota against it,
API billing sums it, pay-per-simulation charges against it, government contracts
report from it. One table, several consumers — not four separate tracking systems.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import String, DateTime, Float, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.core.database import Base


class UsageMetricType(StrEnum):
    # agent_count x ticks_run for one synchronous run — a real compute-workload proxy,
    # deliberately NOT called "agent-hours": these runs are a synchronous burst of
    # simulation ticks, not real wall-clock hours, and claiming otherwise would be the
    # same kind of fabricated precision this project has avoided everywhere else.
    AGENT_TICKS = "agent_ticks"
    API_REQUEST = "api_request"


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    metric_type: Mapped[UsageMetricType] = mapped_column(Enum(UsageMetricType))
    quantity: Mapped[float] = mapped_column(Float)
    environment_key: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

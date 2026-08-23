"""Phase 3 of the multi-tenant platform plan — subscription plans and a simulated
credits ledger. Deliberately NOT wired to any real payment gateway: credits are
granted manually by a super_admin (the "top up" action) and consumed automatically
by real usage, mirroring how every other credential in this project is a local test
value rather than something that moves real money.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import String, DateTime, Float, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.core.database import Base


class CreditTransactionType(StrEnum):
    GRANT = "grant"            # manual top-up by a super_admin
    CONSUMPTION = "consumption"  # automatic debit from real usage (Twin Platform runs)
    ADJUSTMENT = "adjustment"  # manual correction, can be positive or negative


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    type: Mapped[CreditTransactionType] = mapped_column(Enum(CreditTransactionType))
    # Positive for grants/positive adjustments, negative for consumption/negative adjustments.
    amount: Mapped[float] = mapped_column(Float)
    balance_after: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

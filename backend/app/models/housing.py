"""Phase 5 models: Housing & Real Estate."""

import uuid
from datetime import datetime

from sqlalchemy import Float, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.core.database import Base


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    property_type: Mapped[str] = mapped_column(String(50))  # apartment, house, condo, studio, penthouse, shelter
    district_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("districts.id"), nullable=True)

    market_value: Mapped[float] = mapped_column(Float, default=100000.0)
    monthly_rent: Mapped[float] = mapped_column(Float, default=800.0)
    size_sqm: Mapped[int] = mapped_column(Integer, default=60)
    quality: Mapped[float] = mapped_column(Float, default=0.6)
    condition: Mapped[float] = mapped_column(Float, default=0.8)

    is_occupied: Mapped[bool] = mapped_column(Boolean, default=False)
    is_for_sale: Mapped[bool] = mapped_column(Boolean, default=False)
    is_for_rent: Mapped[bool] = mapped_column(Boolean, default=True)

    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("citizens.id"), nullable=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("citizens.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PropertyTransaction(Base):
    __tablename__ = "property_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("properties.id"))
    transaction_type: Mapped[str] = mapped_column(String(30))  # rent_payment, purchase, sale, eviction
    amount: Mapped[float] = mapped_column(Float, default=0.0)

    buyer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("citizens.id"), nullable=True)
    seller_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("citizens.id"), nullable=True)

    sim_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

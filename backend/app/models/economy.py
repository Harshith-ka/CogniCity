import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Float, Integer, String, DateTime, Text, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.app.core.database import Base


class BusinessType(StrEnum):
    RESTAURANT = "restaurant"
    GROCERY = "grocery"
    RETAIL = "retail"
    HOSPITAL = "hospital"
    SCHOOL = "school"
    OFFICE = "office"
    FACTORY = "factory"
    GYM = "gym"
    ENTERTAINMENT = "entertainment"
    BANK = "bank"
    GOVERNMENT = "government"


class TransactionType(StrEnum):
    SALARY = "salary"
    PURCHASE = "purchase"
    RENT = "rent"
    TAX = "tax"
    LOAN = "loan"
    LOAN_REPAYMENT = "loan_repayment"
    INVESTMENT = "investment"
    TRANSFER = "transfer"


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    business_type: Mapped[BusinessType] = mapped_column(Enum(BusinessType))
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizens.id"), nullable=True
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True
    )

    revenue: Mapped[float] = mapped_column(Float, default=0.0)
    expenses: Mapped[float] = mapped_column(Float, default=0.0)
    balance: Mapped[float] = mapped_column(Float, default=10000.0)
    inventory: Mapped[dict] = mapped_column(JSON, default=dict)
    price_multiplier: Mapped[float] = mapped_column(Float, default=1.0)

    max_employees: Mapped[int] = mapped_column(Integer, default=10)
    base_salary: Mapped[float] = mapped_column(Float, default=3000.0)

    is_open: Mapped[bool] = mapped_column(default=True)
    operating_hours: Mapped[dict] = mapped_column(
        JSON, default=lambda: {"open": 9, "close": 17}
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    employees: Mapped[list["Employment"]] = relationship(back_populates="business")

    def __repr__(self) -> str:
        return f"<Business {self.name} type={self.business_type}>"


class Employment(Base):
    __tablename__ = "employments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizens.id"), index=True
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("businesses.id"), index=True
    )

    role: Mapped[str] = mapped_column(String(100))
    salary: Mapped[float] = mapped_column(Float)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    citizen: Mapped["Citizen"] = relationship(back_populates="employments")
    business: Mapped["Business"] = relationship(back_populates="employees")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizens.id"), index=True
    )
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    amount: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(String(500), default="")

    counterparty_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    business_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=True
    )

    sim_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    citizen: Mapped["Citizen"] = relationship(back_populates="transactions")


from backend.app.models.citizen import Citizen  # noqa: E402

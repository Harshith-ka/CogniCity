import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Float, String, DateTime, Text, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.core.database import Base


class DepartmentType(StrEnum):
    MAYOR = "mayor"
    POLICE = "police"
    HEALTHCARE = "healthcare"
    FIRE = "fire"
    EDUCATION = "education"
    TRANSPORT = "transport"
    POWER = "power"
    WATER = "water"
    WASTE = "waste"
    TREASURY = "treasury"


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    department_type: Mapped[DepartmentType] = mapped_column(Enum(DepartmentType), unique=True)

    budget: Mapped[float] = mapped_column(Float, default=100000.0)
    efficiency: Mapped[float] = mapped_column(Float, default=0.7)
    employee_count: Mapped[int] = mapped_column(default=10)

    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    policies: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    department: Mapped[DepartmentType] = mapped_column(Enum(DepartmentType))

    tax_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)

    is_active: Mapped[bool] = mapped_column(default=True)
    approval_rating: Mapped[float] = mapped_column(Float, default=0.5)

    enacted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

"""Phase 5 models: Education & Skills."""

import uuid
from datetime import datetime

from sqlalchemy import Float, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.core.database import Base


class School(Base):
    __tablename__ = "schools"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    school_type: Mapped[str] = mapped_column(String(50))  # elementary, high_school, university, vocational, online
    district_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("districts.id"), nullable=True)
    # Exact sim-world placement — nullable for pre-existing/auto-generated schools that
    # only ever had a district; a manually placed one (via Build Mode) always sets these.
    x: Mapped[float | None] = mapped_column(Float, nullable=True)
    y: Mapped[float | None] = mapped_column(Float, nullable=True)

    capacity: Mapped[int] = mapped_column(Integer, default=200)
    enrolled: Mapped[int] = mapped_column(Integer, default=0)
    teachers: Mapped[int] = mapped_column(Integer, default=15)
    quality_rating: Mapped[float] = mapped_column(Float, default=0.7)
    tuition: Mapped[float] = mapped_column(Float, default=0.0)
    programs: Mapped[list] = mapped_column(JSON, default=list)  # ["engineering", "medicine", "business", "arts"]
    graduation_rate: Mapped[float] = mapped_column(Float, default=0.8)
    is_operational: Mapped[bool] = mapped_column(Boolean, default=True)


class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    citizen_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("citizens.id"))
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id"))
    program: Mapped[str] = mapped_column(String(100), default="general")

    progress: Mapped[float] = mapped_column(Float, default=0.0)
    gpa: Mapped[float] = mapped_column(Float, default=3.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_graduated: Mapped[bool] = mapped_column(Boolean, default=False)

    skills_gained: Mapped[list] = mapped_column(JSON, default=list)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    graduated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CitizenSkill(Base):
    __tablename__ = "citizen_skills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    citizen_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("citizens.id"))
    skill_name: Mapped[str] = mapped_column(String(100))
    proficiency: Mapped[float] = mapped_column(Float, default=0.1)  # 0.0 to 1.0
    source: Mapped[str] = mapped_column(String(50), default="self_taught")  # school, job, self_taught, mentor
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

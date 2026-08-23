"""Platform auth models — Phase 1 of the multi-tenant admin portal plan.

Deliberately named PlatformUser (not User) and kept in their own module: this app
already has a `Citizen` model representing simulated people, and these tables
represent real humans logging into the admin portal to manage organizations. The two
concepts must never be confused with each other in code or in the database.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import String, DateTime, Boolean, Enum, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.app.core.database import Base


class UserRole(StrEnum):
    SUPER_ADMIN = "super_admin"   # platform-wide — creates/manages every organization
    ORG_ADMIN = "org_admin"       # manages their own organization's users
    ORG_MEMBER = "org_member"     # uses the platform within their org's quota


class OrganizationStatus(StrEnum):
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    status: Mapped[OrganizationStatus] = mapped_column(Enum(OrganizationStatus), default=OrganizationStatus.TRIAL)

    # Plan enforcement fields — a real Plan table with billing comes in a later phase;
    # for Phase 1 (auth + isolation) these plain fields are enough to prove the model.
    plan_key: Mapped[str] = mapped_column(String(50), default="basic")  # basic|pro|enterprise|research
    agent_quota: Mapped[int] = mapped_column(Integer, default=1000)
    model_tier: Mapped[str] = mapped_column(String(20), default="simplified")  # simplified|advanced

    # Which Twin Platform environment keys (from EnvironmentRegistry — "city",
    # "hospital_ward", etc.) this org may run. An EMPTY list means unrestricted — this
    # is the backward-compatible default so every org created before this column
    # existed keeps working exactly as before with zero migration step.
    allowed_environments: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Which city-simulation feature modules ("tabs" — Traffic, Disasters, AI Advisor,
    # ...) this org may call, scoped independently of allowed_environments: an org can
    # have full environment access but a Basic-tier subset of feature modules, or vice
    # versa. Same empty-list-means-unrestricted convention as allowed_environments.
    allowed_modules: Mapped[list[str]] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    users: Mapped[list["PlatformUser"]] = relationship(back_populates="organization")


class PlatformUser(Base):
    __tablename__ = "platform_users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Nullable only for the super_admin — every org_admin/org_member must belong to
    # exactly one organization; enforced in the API layer, not the DB, since a super
    # admin genuinely has no org to belong to.
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.ORG_MEMBER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped["Organization | None"] = relationship(back_populates="users")

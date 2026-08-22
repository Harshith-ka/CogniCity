"""Admin portal — organization & user management (Phase 1).

Every route here proves tenant isolation, not just role-gating: a super_admin can see
everything, but an org_admin querying another organization's users gets a 403, not a
filtered empty list — the difference matters because a filtered-empty response still
implicitly confirms the org's existence to someone who shouldn't know that.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.dependencies import get_current_user, require_org_access, require_roles
from backend.app.auth.security import hash_password
from backend.app.core.database import get_db
from backend.app.models.auth import Organization, OrganizationStatus, PlatformUser, UserRole

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ─────────────────────────────────────────────────────────────
# Organizations — super_admin only
# ─────────────────────────────────────────────────────────────

class OrgCreateRequest(BaseModel):
    name: str
    plan_key: str = "basic"
    agent_quota: int = 1000
    model_tier: str = "simplified"


class OrgOut(BaseModel):
    id: str
    name: str
    status: str
    plan_key: str
    agent_quota: int
    model_tier: str
    user_count: int = 0


def _to_org_out(org: Organization, user_count: int = 0) -> OrgOut:
    return OrgOut(
        id=str(org.id), name=org.name, status=org.status.value, plan_key=org.plan_key,
        agent_quota=org.agent_quota, model_tier=org.model_tier, user_count=user_count,
    )


@router.post("/organizations", response_model=OrgOut)
async def create_organization(
    req: OrgCreateRequest,
    db: AsyncSession = Depends(get_db),
    _admin: PlatformUser = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    existing = await db.execute(select(Organization).where(Organization.name == req.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Organization {req.name!r} already exists")

    org = Organization(
        name=req.name, plan_key=req.plan_key, agent_quota=req.agent_quota, model_tier=req.model_tier,
        status=OrganizationStatus.TRIAL,
    )
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return _to_org_out(org)


@router.get("/organizations", response_model=list[OrgOut])
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    _admin: PlatformUser = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    result = await db.execute(select(Organization))
    orgs = list(result.scalars().all())
    out = []
    for org in orgs:
        count_result = await db.execute(select(PlatformUser).where(PlatformUser.organization_id == org.id))
        out.append(_to_org_out(org, len(list(count_result.scalars().all()))))
    return out


@router.get("/organizations/{org_id}", response_model=OrgOut)
async def get_organization(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: PlatformUser = Depends(require_org_access),
):
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    count_result = await db.execute(select(PlatformUser).where(PlatformUser.organization_id == org.id))
    return _to_org_out(org, len(list(count_result.scalars().all())))


# ─────────────────────────────────────────────────────────────
# Users within an organization — org_admin (own org) or super_admin (any org)
# ─────────────────────────────────────────────────────────────

class OrgUserCreateRequest(BaseModel):
    email: str
    password: str
    name: str
    role: UserRole = UserRole.ORG_MEMBER


class OrgUserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool


def _to_org_user_out(user: PlatformUser) -> OrgUserOut:
    return OrgUserOut(id=str(user.id), email=user.email, name=user.name, role=user.role.value, is_active=user.is_active)


@router.get("/organizations/{org_id}/users", response_model=list[OrgUserOut])
async def list_organization_users(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: PlatformUser = Depends(require_org_access),
):
    result = await db.execute(select(PlatformUser).where(PlatformUser.organization_id == org_id))
    return [_to_org_user_out(u) for u in result.scalars().all()]


@router.post("/organizations/{org_id}/users", response_model=OrgUserOut)
async def create_organization_user(
    org_id: uuid.UUID,
    req: OrgUserCreateRequest,
    db: AsyncSession = Depends(get_db),
    caller: PlatformUser = Depends(require_org_access),
):
    if req.role == UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=400, detail="Cannot create a super_admin through this endpoint")
    # An org_admin may only create members/admins within their own org — require_org_access
    # already enforced that caller belongs to org_id (or is a super_admin), so this is safe.
    if caller.role == UserRole.ORG_MEMBER:
        raise HTTPException(status_code=403, detail="Only an org_admin can add users")

    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    existing = await db.execute(select(PlatformUser).where(PlatformUser.email == req.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"A user with email {req.email!r} already exists")

    user = PlatformUser(
        organization_id=org_id, email=req.email.lower(), name=req.name,
        hashed_password=hash_password(req.password), role=req.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _to_org_user_out(user)

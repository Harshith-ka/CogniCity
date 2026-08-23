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
from backend.app.core.feature_modules import FEATURE_MODULES
from backend.app.core.plans import PLANS
from backend.app.models.auth import Organization, OrganizationStatus, PlatformUser, UserRole
from backend.app.services.billing import grant_credits, get_billing_summary, subscribe_to_plan, UnknownPlanError
from backend.app.services.usage_metering import get_usage_summary

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/feature-modules")
async def list_feature_modules():
    """The catalog the admin UI renders as checkboxes — same public-catalog pattern
    as GET /api/twin-platform/environments."""
    return FEATURE_MODULES


@router.get("/plans")
async def list_plans():
    """Subscription plan catalog (Phase 3) — same public-catalog pattern as
    feature-modules and the Twin Platform's environment list."""
    return PLANS


# ─────────────────────────────────────────────────────────────
# Organizations — super_admin only
# ─────────────────────────────────────────────────────────────

class OrgCreateRequest(BaseModel):
    name: str
    plan_key: str = "basic"
    agent_quota: int = 1000
    model_tier: str = "simplified"
    allowed_environments: list[str] = []
    allowed_modules: list[str] = []


class OrgOut(BaseModel):
    id: str
    name: str
    status: str
    plan_key: str
    agent_quota: int
    model_tier: str
    allowed_environments: list[str] = []
    allowed_modules: list[str] = []
    credits_balance: float = 0.0
    user_count: int = 0


def _to_org_out(org: Organization, user_count: int = 0) -> OrgOut:
    return OrgOut(
        id=str(org.id), name=org.name, status=org.status.value, plan_key=org.plan_key,
        agent_quota=org.agent_quota, model_tier=org.model_tier,
        allowed_environments=org.allowed_environments or [],
        allowed_modules=org.allowed_modules or [], credits_balance=org.credits_balance,
        user_count=user_count,
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
        allowed_environments=req.allowed_environments, allowed_modules=req.allowed_modules,
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


class OrgEnvironmentsUpdateRequest(BaseModel):
    allowed_environments: list[str]


@router.put("/organizations/{org_id}/environments", response_model=OrgOut)
async def set_organization_environments(
    org_id: uuid.UUID,
    req: OrgEnvironmentsUpdateRequest,
    db: AsyncSession = Depends(get_db),
    # Entitlements gate what an org's plan includes — that's a billing-tier decision,
    # not something an org_admin should be able to grant themselves, so this is
    # platform-admin only (unlike the org-scoped user/usage endpoints above).
    _admin: PlatformUser = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    org.allowed_environments = req.allowed_environments
    await db.commit()
    await db.refresh(org)
    count_result = await db.execute(select(PlatformUser).where(PlatformUser.organization_id == org.id))
    return _to_org_out(org, len(list(count_result.scalars().all())))


class OrgModulesUpdateRequest(BaseModel):
    allowed_modules: list[str]


@router.put("/organizations/{org_id}/modules", response_model=OrgOut)
async def set_organization_modules(
    org_id: uuid.UUID,
    req: OrgModulesUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _admin: PlatformUser = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    org.allowed_modules = req.allowed_modules
    await db.commit()
    await db.refresh(org)
    count_result = await db.execute(select(PlatformUser).where(PlatformUser.organization_id == org.id))
    return _to_org_out(org, len(list(count_result.scalars().all())))


@router.get("/organizations/{org_id}/usage")
async def get_organization_usage(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: PlatformUser = Depends(require_org_access),
):
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {
        "organization_id": str(org_id),
        "agent_quota": org.agent_quota,
        "usage": await get_usage_summary(db, org_id),
    }


class OrgPlanUpdateRequest(BaseModel):
    plan_key: str


@router.put("/organizations/{org_id}/plan", response_model=OrgOut)
async def set_organization_plan(
    org_id: uuid.UUID,
    req: OrgPlanUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _admin: PlatformUser = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    from backend.app.core.plans import PLAN_BY_KEY

    plan = PLAN_BY_KEY.get(req.plan_key)
    if not plan:
        raise HTTPException(status_code=400, detail=f"Unknown plan key {req.plan_key!r}")

    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    org.plan_key = plan["key"]
    org.agent_quota = plan["agent_quota"]
    org.model_tier = plan["model_tier"]
    org.allowed_environments = list(plan.get("allowed_environments", []))
    org.allowed_modules = list(plan.get("allowed_modules", []))
    await db.commit()
    await db.refresh(org)
    count_result = await db.execute(select(PlatformUser).where(PlatformUser.organization_id == org.id))
    return _to_org_out(org, len(list(count_result.scalars().all())))


class SubscribeRequest(BaseModel):
    plan_key: str


@router.post("/organizations/{org_id}/subscribe", response_model=OrgOut)
async def subscribe_organization(
    org_id: uuid.UUID,
    req: SubscribeRequest,
    db: AsyncSession = Depends(get_db),
    # Self-service — an org_admin can upgrade their own org's plan (require_org_access
    # allows the org's own admin, not just super_admin). Unlike the raw PUT /plan
    # override above, this is the "purchase" action and grants that plan's credits.
    caller: PlatformUser = Depends(require_org_access),
):
    if caller.role == UserRole.ORG_MEMBER:
        raise HTTPException(status_code=403, detail="Only an org_admin can change the organization's plan")

    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    try:
        org = await subscribe_to_plan(db, org, req.plan_key)
    except UnknownPlanError as err:
        raise HTTPException(status_code=400, detail=str(err))

    count_result = await db.execute(select(PlatformUser).where(PlatformUser.organization_id == org.id))
    return _to_org_out(org, len(list(count_result.scalars().all())))


@router.get("/organizations/{org_id}/billing")
async def get_organization_billing(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: PlatformUser = Depends(require_org_access),
):
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return await get_billing_summary(db, org)


class GrantCreditsRequest(BaseModel):
    amount: float
    description: str = "Manual credit grant"


@router.post("/organizations/{org_id}/credits", response_model=OrgOut)
async def grant_organization_credits(
    org_id: uuid.UUID,
    req: GrantCreditsRequest,
    db: AsyncSession = Depends(get_db),
    # There's no real payment gateway behind this — this IS the "purchase" action,
    # a manual top-up a super_admin performs on an org's behalf. Same reasoning as
    # entitlements: a billing-tier action, not something an org grants itself.
    _admin: PlatformUser = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Grant amount must be positive")
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    org = await grant_credits(db, org, req.amount, req.description)
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

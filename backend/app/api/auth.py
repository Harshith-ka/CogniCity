"""Admin portal authentication — Phase 1 of the multi-tenant platform plan.

Session-cookie based (httpOnly JWT), separate entirely from the simulation's own API,
which stays open exactly as it is today. Nothing here changes how the dashboard or
3D view work.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.dependencies import SESSION_COOKIE_NAME, get_current_user
from backend.app.auth.security import create_access_token, hash_password, verify_password
from backend.app.core.database import get_db
from backend.app.core.plans import PLAN_BY_KEY
from backend.app.models.auth import Organization, OrganizationStatus, PlatformUser, UserRole
from backend.app.services.billing import grant_credits

router = APIRouter(prefix="/api/auth", tags=["auth"])

# httpOnly so JS can't read the token (XSS-safe); secure=False only because local dev
# runs over plain http — this MUST become True behind real TLS.
COOKIE_KWARGS = {"httponly": True, "samesite": "lax", "secure": False, "max_age": 60 * 60 * 24}


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    organization_id: str | None
    organization_name: str | None = None
    # Only populated on POST /login — a non-browser client (the mobile app) has no
    # httpOnly cookie jar to rely on, so it needs the raw JWT once, up front, to
    # replay as `Authorization: Bearer <token>` on every later request. GET /me never
    # sets this: it authenticates via a token the client already has, so re-issuing it
    # here would just be redundant exposure.
    token: str | None = None


def _to_user_out(user: PlatformUser, org_name: str | None = None, token: str | None = None) -> UserOut:
    return UserOut(
        id=str(user.id), email=user.email, name=user.name, role=user.role.value,
        organization_id=str(user.organization_id) if user.organization_id else None,
        organization_name=org_name, token=token,
    )


@router.post("/login", response_model=UserOut)
async def login(req: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlatformUser).where(PlatformUser.email == req.email.lower()))
    user = result.scalar_one_or_none()
    if not user or not user.is_active or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    token = create_access_token(
        subject=str(user.id),
        extra_claims={"role": user.role.value, "org_id": str(user.organization_id) if user.organization_id else None},
    )
    response.set_cookie(SESSION_COOKIE_NAME, token, **COOKIE_KWARGS)

    org_name = None
    if user.organization_id:
        org = await db.get(Organization, user.organization_id)
        org_name = org.name if org else None
    return _to_user_out(user, org_name, token=token)


class SignupRequest(BaseModel):
    email: str
    password: str
    name: str
    organization_name: str


@router.post("/signup", response_model=UserOut)
async def signup(req: SignupRequest, response: Response, db: AsyncSession = Depends(get_db)):
    """Self-service account creation — no invite needed. Every self-signup lands on
    the free Trial plan (see backend/app/core/plans.py: 3 simulation runs, small
    quota/credits) and becomes org_admin of their own brand-new organization, since
    there's no existing admin to have invited them into one. Upgrading off the trial
    happens via POST /organizations/{id}/subscribe once they're logged in."""
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    existing_user = await db.execute(select(PlatformUser).where(PlatformUser.email == req.email.lower()))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"A user with email {req.email!r} already exists")

    existing_org = await db.execute(select(Organization).where(Organization.name == req.organization_name))
    if existing_org.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Organization {req.organization_name!r} already exists")

    trial = PLAN_BY_KEY["trial"]
    org = Organization(
        name=req.organization_name, status=OrganizationStatus.TRIAL,
        plan_key=trial["key"], agent_quota=trial["agent_quota"], model_tier=trial["model_tier"],
        allowed_environments=list(trial["allowed_environments"]), allowed_modules=list(trial["allowed_modules"]),
    )
    db.add(org)
    await db.flush()  # assigns org.id without a full commit yet
    await grant_credits(db, org, trial["included_credits"], "Welcome — free trial credits")

    user = PlatformUser(
        organization_id=org.id, email=req.email.lower(), name=req.name,
        hashed_password=hash_password(req.password), role=UserRole.ORG_ADMIN,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(
        subject=str(user.id),
        extra_claims={"role": user.role.value, "org_id": str(org.id)},
    )
    response.set_cookie(SESSION_COOKIE_NAME, token, **COOKIE_KWARGS)
    return _to_user_out(user, org.name, token=token)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"status": "logged_out"}


@router.get("/me", response_model=UserOut)
async def me(user: PlatformUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_name = None
    if user.organization_id:
        org = await db.get(Organization, user.organization_id)
        org_name = org.name if org else None
    return _to_user_out(user, org_name)

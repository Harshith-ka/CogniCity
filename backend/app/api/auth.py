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
from backend.app.models.auth import Organization, PlatformUser, UserRole

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

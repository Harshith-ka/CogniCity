"""FastAPI dependencies for admin-portal auth — session cookie in, PlatformUser out.

Deliberately not applied to any existing simulation/dashboard route in Phase 1. This
is a new, additive layer for the /api/auth and /api/admin routers only, so the
already-running dashboard and 3D view keep working exactly as they do today.
"""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.security import decode_access_token
from backend.app.core.database import get_db
from backend.app.models.auth import Organization, PlatformUser, UserRole

SESSION_COOKIE_NAME = "cognicity_session"


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> PlatformUser:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    claims = decode_access_token(token)
    if not claims:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")

    user = await db.get(PlatformUser, uuid.UUID(claims["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


async def get_current_user_optional(request: Request, db: AsyncSession = Depends(get_db)) -> PlatformUser | None:
    """Same lookup as get_current_user, but returns None instead of raising — for
    routes like the Twin Platform run endpoint that must keep working unauthenticated
    (Phase 1's "never break existing functionality" principle) while still metering
    usage for whoever *is* logged in."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
    if not token:
        return None

    claims = decode_access_token(token)
    if not claims:
        return None

    user = await db.get(PlatformUser, uuid.UUID(claims["sub"]))
    if not user or not user.is_active:
        return None
    return user


def require_roles(*allowed: UserRole):
    """Dependency factory: require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)."""
    async def _check(user: PlatformUser = Depends(get_current_user)) -> PlatformUser:
        if user.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return _check


async def require_org_access(org_id: uuid.UUID, user: PlatformUser = Depends(get_current_user)) -> PlatformUser:
    """A super_admin can access any organization; everyone else only their own —
    this is the actual tenant-isolation check, not just a role check."""
    if user.role == UserRole.SUPER_ADMIN:
        return user
    if user.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this organization")
    return user


def require_feature(module_key: str):
    """Dependency factory gating a whole router behind a feature-module entitlement —
    wired in at app.include_router(..., dependencies=[Depends(require_feature("x"))])
    rather than inside each router file, so the routers themselves stay untouched.

    Same additive pattern as the Twin Platform run endpoint's quota check: an
    unauthenticated caller (today's fully-open API) or a platform-root user with no
    organization is never restricted. Only a logged-in org member whose org has a
    non-empty allowed_modules list that excludes this module gets a 403 — every
    existing org (empty list = unrestricted) keeps working exactly as before.
    """
    async def _check(
        user: PlatformUser | None = Depends(get_current_user_optional),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        if not user or not user.organization_id:
            return
        org = await db.get(Organization, user.organization_id)
        if org and org.allowed_modules and module_key not in org.allowed_modules:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{org.name}'s plan does not include the {module_key!r} module",
            )
    return _check

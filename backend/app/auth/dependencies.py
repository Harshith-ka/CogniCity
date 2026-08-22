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
from backend.app.models.auth import PlatformUser, UserRole

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

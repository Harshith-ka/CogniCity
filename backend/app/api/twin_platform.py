"""Twin Platform API: the environment catalog (marketplace MVP) — list what's
available and run one by key, without the caller needing to know which Python class
implements it."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.dependencies import get_current_user_optional
from backend.app.core.database import get_db
from backend.app.models.auth import PlatformUser
from backend.app.models.usage import UsageMetricType
from backend.app.services.usage_metering import QuotaExceededError, check_agent_quota, record_usage
from backend.app.twin_platform.registry import EnvironmentRegistry

router = APIRouter(prefix="/api/twin-platform", tags=["twin_platform"])

# CityTwin wraps the live production simulation over HTTP — a single real tick can
# take from several seconds up to a couple of minutes depending on population and
# whether LLM-backed decisions are in play, so a synchronous "run 10 ticks" request
# against it would be a very long-held HTTP request. Cap it here rather than let a
# careless request hang the endpoint.
MAX_TICKS_LIVE_CITY = 2
MAX_TICKS_SANDBOX = 200


@router.get("/environments")
async def list_environments():
    return [
        {
            "key": m.key,
            "name": m.name,
            "category": m.category,
            "icon": m.icon,
            "description": m.description,
            "default_config": m.default_config,
            "entity_types": m.entity_types,
            "scenario_examples": m.scenario_examples,
        }
        for m in EnvironmentRegistry.list()
    ]


class RunEnvironmentRequest(BaseModel):
    config: dict = {}
    initial_agents: int = 0
    ticks: int = 10
    event_type: str | None = None
    event_at_tick: int | None = None  # defaults to halfway through the run
    event_params: dict = {}


@router.post("/environments/{key}/run")
async def run_environment(
    key: str,
    req: RunEnvironmentRequest,
    db: AsyncSession = Depends(get_db),
    user: PlatformUser | None = Depends(get_current_user_optional),
):
    manifest = EnvironmentRegistry.get(key)
    if not manifest:
        raise HTTPException(status_code=404, detail=f"Unknown environment: {key!r}")

    # Metering/entitlement only applies to a logged-in user tied to an organization —
    # an unauthenticated call (the existing, currently-open marketplace UI) runs
    # exactly as it did before Phase 2, with no checks and nothing recorded.
    org = None
    if user and user.organization_id:
        from backend.app.models.auth import Organization
        org = await db.get(Organization, user.organization_id)
        if org:
            # allowed_environments == [] means unrestricted (the pre-entitlement
            # default) — only a non-empty allow-list actually restricts access.
            if org.allowed_environments and key not in org.allowed_environments:
                raise HTTPException(
                    status_code=403,
                    detail=f"{org.name}'s plan does not include the {manifest.name!r} environment",
                )
            if req.initial_agents:
                try:
                    check_agent_quota(org, req.initial_agents)
                except QuotaExceededError as err:
                    raise HTTPException(status_code=402, detail=str(err))

    max_ticks = MAX_TICKS_LIVE_CITY if key == "city" else MAX_TICKS_SANDBOX
    ticks = min(req.ticks, max_ticks)

    try:
        env = await EnvironmentRegistry.create(key, req.config)
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"Failed to initialize environment: {err}")

    if req.initial_agents:
        await env.spawn_agents(req.initial_agents)

    event_tick = req.event_at_tick if req.event_at_tick is not None else ticks // 2
    triggered_event = None
    tick_log = []

    for i in range(ticks):
        if req.event_type and i == event_tick:
            triggered_event = await env.generate_event(req.event_type, **req.event_params)
        tick_log.append(await env.step())

    if org:
        await record_usage(
            db, org.id, UsageMetricType.API_REQUEST, quantity=1, environment_key=key,
        )
        if req.initial_agents:
            await record_usage(
                db, org.id, UsageMetricType.AGENT_TICKS,
                quantity=req.initial_agents * ticks, environment_key=key,
            )

    return {
        "environment": key,
        "ticks_run": ticks,
        "ticks_requested": req.ticks,
        "capped": ticks < req.ticks,
        "triggered_event": triggered_event,
        "final_metrics": await env.evaluate(),
        "final_state": await env.get_state(),
        "tick_log": tick_log,
    }

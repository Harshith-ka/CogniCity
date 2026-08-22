"""API routes for city events."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.events.event_engine import EventEngine, EVENT_TEMPLATES
from backend.app.government.government_ai import GovernmentAI
from backend.app.models.event import CityEvent

router = APIRouter(prefix="/events", tags=["events"])


class TriggerEventRequest(BaseModel):
    event_name: str | None = None
    area_x: float | None = None
    area_y: float | None = None
    radius: float = 500.0


@router.get("/")
async def list_events(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    query = select(CityEvent)
    if active_only:
        query = query.where(CityEvent.is_active == True)  # noqa: E712

    result = await db.execute(query)
    events = list(result.scalars().all())
    return [
        {
            "id": str(e.id),
            "name": e.name,
            "category": e.category.value,
            "severity": e.severity.value,
            "description": e.description,
            "remaining_ticks": e.remaining_ticks,
            "is_active": e.is_active,
            "is_citywide": e.affected_area_x is None or e.affected_area_y is None,
            "affected_area_x": e.affected_area_x,
            "affected_area_y": e.affected_area_y,
            "affected_radius": e.affected_radius,
        }
        for e in events
    ]


@router.post("/trigger")
async def trigger_event(
    req: TriggerEventRequest,
    db: AsyncSession = Depends(get_db),
):
    engine = EventEngine(db)
    event = await engine.trigger_event(
        template_name=req.event_name,
        area_x=req.area_x,
        area_y=req.area_y,
        radius=req.radius,
    )

    gov = GovernmentAI(db)
    gov_decisions = await gov.emergency_response(
        event_name=event.name,
        category=event.category.value,
        severity=event.severity.value,
        sim_time=event.sim_started_at,
    )
    await db.commit()

    return {
        "id": str(event.id),
        "name": event.name,
        "category": event.category.value,
        "severity": event.severity.value,
        "description": event.description,
        "government_response": gov_decisions,
    }


@router.get("/templates")
async def list_event_templates():
    return [
        {
            "name": t["name"],
            "category": t["category"].value,
            "severity": t["severity"].value,
            "description": t["description"],
            "duration": t["duration"],
        }
        for t in EVENT_TEMPLATES
    ]

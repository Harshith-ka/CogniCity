"""Phase 3 API: Disaster simulation endpoints."""

import math
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.disasters.disaster_engine import DisasterEngine
from backend.app.government.government_ai import GovernmentAI
from backend.app.models.city import District
from backend.app.models.disaster import DisasterType, DisasterPhase, EvacuationZone, Disaster
from backend.app.models.healthcare import Hospital
from backend.app.engine.world_clock import WorldClock

router = APIRouter(prefix="/api/disasters", tags=["disasters"])

RESPONSE_PHASE_NARRATIVE = {
    "onset": "Units mobilizing — dispatch in progress.",
    "peak": "Active response — crews on-site managing the emergency.",
    "declining": "Situation stabilizing — response scaling down.",
    "recovery": "Cleanup and recovery crews active.",
    "resolved": "Response stood down — disaster resolved.",
}


class TriggerDisasterRequest(BaseModel):
    disaster_type: str
    epicenter_x: float | None = None
    epicenter_y: float | None = None
    intensity: float = 0.7


@router.get("/active")
async def get_active_disasters(db: AsyncSession = Depends(get_db)):
    engine = DisasterEngine(db)
    return await engine.get_active_disasters()


async def _resolve_disasters(db: AsyncSession, disasters: list[Disaster]) -> int:
    """Force-end disasters immediately, regardless of simulation tick state — the
    engine only auto-resolves a disaster when elapsed_ticks catches up with
    duration_ticks, which never happens while the simulation is paused/stopped, so a
    triggered disaster otherwise sits active indefinitely with no way to clear it."""
    if not disasters:
        return 0
    now = datetime.utcnow()
    for d in disasters:
        d.is_active = False
        d.phase = DisasterPhase.RESOLVED
        d.ended_at = now
    await db.execute(
        update(EvacuationZone)
        .where(EvacuationZone.disaster_id.in_([d.id for d in disasters]))
        .values(is_active=False)
    )
    await db.commit()
    return len(disasters)


@router.post("/{disaster_id}/resolve")
async def resolve_disaster(disaster_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    disaster = await db.get(Disaster, disaster_id)
    if not disaster:
        raise HTTPException(status_code=404, detail="Disaster not found")
    await _resolve_disasters(db, [disaster])
    return {"status": "resolved", "id": str(disaster.id)}


@router.post("/resolve-all")
async def resolve_all_disasters(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Disaster).where(Disaster.is_active == True))  # noqa: E712
    count = await _resolve_disasters(db, list(result.scalars().all()))
    return {"status": "resolved", "count": count}


@router.get("/evacuation-zones")
async def get_evacuation_zones(db: AsyncSession = Depends(get_db)):
    # Joined against currently-active disasters rather than trusting is_active alone —
    # zones don't always get flipped off in lockstep with their parent disaster resolving.
    result = await db.execute(
        select(EvacuationZone)
        .join(Disaster, Disaster.id == EvacuationZone.disaster_id)
        .where(EvacuationZone.is_active == True, Disaster.is_active == True)  # noqa: E712
    )
    zones = list(result.scalars().all())
    return [
        {
            "id": str(z.id),
            "disaster_id": str(z.disaster_id),
            "name": z.name,
            "center": [z.center_x, z.center_y],
            "radius": round(z.radius, 1),
            "evacuees": z.evacuees,
            "capacity": z.capacity,
        }
        for z in zones
    ]


@router.get("/{disaster_id}/response")
async def get_disaster_response(disaster_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Who's actually responding: which hospitals dispatched staff, and how many
    police/ambulance/fire units — computed deterministically from the disaster's own
    severity fields so these numbers are the same ones the 3D view spawns as vehicles,
    not an independent random count."""
    disaster = await db.get(Disaster, disaster_id)
    if not disaster:
        raise HTTPException(status_code=404, detail="Disaster not found")

    hospitals_result = await db.execute(select(Hospital).where(Hospital.is_operational.is_(True)))
    hospitals = hospitals_result.scalars().all()
    districts_result = await db.execute(select(District))
    district_by_id = {d.id: d for d in districts_result.scalars().all()}

    dispatched_hospitals = []
    for h in hospitals:
        d = district_by_id.get(h.district_id)
        if not d:
            continue
        dist = math.hypot(d.center_x - disaster.epicenter_x, d.center_y - disaster.epicenter_y)
        if dist <= disaster.radius * 2.5:
            staff_dispatched = min(h.staff_count, max(4, round(h.staff_count * 0.25)))
            dispatched_hospitals.append({
                "name": h.name,
                "district": d.name,
                "distance": round(dist, 1),
                "staff_dispatched": staff_dispatched,
                "total_staff": h.staff_count,
                "beds_available": h.total_beds,
                "icu_beds": h.icu_beds,
            })
    dispatched_hospitals.sort(key=lambda h: h["distance"])

    severity = disaster.intensity
    ambulances = max(1, round(2 + severity * 6 + disaster.injuries / 15))
    police_units = max(1, round(2 + severity * 5 + disaster.casualties / 10))
    fire_trucks = max(2, round(severity * 4)) if disaster.disaster_type.value == "fire" else round(severity * 2)

    total_staff_dispatched = (
        sum(h["staff_dispatched"] for h in dispatched_hospitals)
        + ambulances * 2 + police_units * 2 + fire_trucks * 3
    )

    return {
        "disaster_id": str(disaster.id),
        "phase": disaster.phase.value,
        "status_narrative": RESPONSE_PHASE_NARRATIVE.get(disaster.phase.value, ""),
        "hospitals_responding": dispatched_hospitals[:6],
        "vehicles": {"ambulances": ambulances, "police_units": police_units, "fire_trucks": fire_trucks},
        "total_staff_dispatched": total_staff_dispatched,
    }


@router.get("/history")
async def get_disaster_history(
    limit: int = 20, db: AsyncSession = Depends(get_db)
):
    engine = DisasterEngine(db)
    return await engine.get_disaster_history(limit=limit)


@router.get("/types")
async def get_disaster_types():
    return [t.value for t in DisasterType]


@router.post("/trigger")
async def trigger_disaster(
    req: TriggerDisasterRequest, db: AsyncSession = Depends(get_db)
):
    try:
        dtype = DisasterType(req.disaster_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid disaster type: {req.disaster_type}")

    engine = DisasterEngine(db)
    from datetime import datetime
    sim_time = datetime.utcnow()
    disaster = await engine.trigger_disaster(
        disaster_type=dtype,
        sim_time=sim_time,
        epicenter_x=req.epicenter_x,
        epicenter_y=req.epicenter_y,
        intensity=req.intensity,
    )

    severity = "low" if req.intensity < 0.3 else "medium" if req.intensity < 0.6 else "high" if req.intensity < 0.85 else "critical"
    gov = GovernmentAI(db)
    gov_decisions = await gov.emergency_response(
        event_name=disaster.name, category="natural_disaster", severity=severity, sim_time=sim_time,
    )

    await db.commit()
    return {
        "id": str(disaster.id),
        "name": disaster.name,
        "type": disaster.disaster_type.value,
        "phase": disaster.phase.value,
        "intensity": disaster.intensity,
        "government_response": gov_decisions,
    }

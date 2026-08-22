"""Phase 3 API: Disaster simulation endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.disasters.disaster_engine import DisasterEngine
from backend.app.government.government_ai import GovernmentAI
from backend.app.models.disaster import DisasterType
from backend.app.engine.world_clock import WorldClock

router = APIRouter(prefix="/api/disasters", tags=["disasters"])


class TriggerDisasterRequest(BaseModel):
    disaster_type: str
    epicenter_x: float | None = None
    epicenter_y: float | None = None
    intensity: float = 0.7


@router.get("/active")
async def get_active_disasters(db: AsyncSession = Depends(get_db)):
    engine = DisasterEngine(db)
    return await engine.get_active_disasters()


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

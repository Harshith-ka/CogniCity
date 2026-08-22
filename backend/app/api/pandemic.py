"""Phase 3 API: Pandemic simulation endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.government.government_ai import GovernmentAI
from backend.app.pandemic.pandemic_engine import PandemicEngine

router = APIRouter(prefix="/api/pandemic", tags=["pandemic"])


class StartPandemicRequest(BaseModel):
    name: str = "Novel Virus Outbreak"
    pathogen: str = "NV-1"
    r0: float = 2.5
    infection_rate: float = 0.03
    recovery_rate: float = 0.01
    mortality_rate: float = 0.005
    incubation_ticks: int = 30
    initial_infected: int = 5
    hospital_capacity: int = 50


class LockdownRequest(BaseModel):
    pandemic_id: str
    active: bool


class VaccinationRequest(BaseModel):
    pandemic_id: str
    rate: float = 0.02


@router.get("/stats")
async def get_pandemic_stats(db: AsyncSession = Depends(get_db)):
    engine = PandemicEngine(db)
    return await engine.get_pandemic_stats()


@router.get("/health-records/{pandemic_id}")
async def get_health_records(
    pandemic_id: str, db: AsyncSession = Depends(get_db)
):
    engine = PandemicEngine(db)
    return await engine.get_health_records(pandemic_id)


@router.post("/start")
async def start_pandemic(
    req: StartPandemicRequest, db: AsyncSession = Depends(get_db)
):
    engine = PandemicEngine(db)
    from datetime import datetime
    sim_time = datetime.utcnow()
    pandemic = await engine.start_pandemic(
        name=req.name,
        pathogen=req.pathogen,
        sim_time=sim_time,
        r0=req.r0,
        infection_rate=req.infection_rate,
        recovery_rate=req.recovery_rate,
        mortality_rate=req.mortality_rate,
        incubation_ticks=req.incubation_ticks,
        initial_infected=req.initial_infected,
        hospital_capacity=req.hospital_capacity,
    )

    severity = "low" if req.r0 < 1.2 else "medium" if req.r0 < 2.0 else "high" if req.r0 < 3.0 else "critical"
    gov = GovernmentAI(db)
    gov_decisions = await gov.emergency_response(
        event_name=pandemic.name, category="health", severity=severity, sim_time=sim_time,
    )

    await db.commit()
    return {
        "id": str(pandemic.id),
        "name": pandemic.name,
        "pathogen": pandemic.pathogen,
        "r0": pandemic.r0,
        "government_response": gov_decisions,
    }


@router.post("/lockdown")
async def toggle_lockdown(
    req: LockdownRequest, db: AsyncSession = Depends(get_db)
):
    engine = PandemicEngine(db)
    await engine.toggle_lockdown(req.pandemic_id, req.active)
    await db.commit()
    return {"status": "ok", "lockdown_active": req.active}


@router.post("/mask-mandate")
async def toggle_mask_mandate(
    req: LockdownRequest, db: AsyncSession = Depends(get_db)
):
    engine = PandemicEngine(db)
    await engine.toggle_mask_mandate(req.pandemic_id, req.active)
    await db.commit()
    return {"status": "ok", "mask_mandate": req.active}


@router.post("/vaccinate")
async def start_vaccination(
    req: VaccinationRequest, db: AsyncSession = Depends(get_db)
):
    engine = PandemicEngine(db)
    await engine.start_vaccination(req.pandemic_id, req.rate)
    await db.commit()
    return {"status": "ok", "vaccination_rate": req.rate}

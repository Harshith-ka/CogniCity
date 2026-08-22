"""Phase 5 API: Healthcare endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.healthcare.healthcare_engine import HealthcareEngine
from backend.app.models.healthcare import Hospital, MedicalRecord

router = APIRouter(prefix="/api/healthcare", tags=["healthcare"])


@router.get("/stats")
async def healthcare_stats(db: AsyncSession = Depends(get_db)):
    engine = HealthcareEngine(db)
    return await engine.get_stats()


@router.get("/hospitals")
async def list_hospitals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Hospital))
    return [{
        "id": str(h.id),
        "name": h.name,
        "type": h.hospital_type,
        "total_beds": h.total_beds,
        "occupied_beds": h.occupied_beds,
        "icu_beds": h.icu_beds,
        "icu_occupied": h.icu_occupied,
        "staff_count": h.staff_count,
        "quality_rating": h.quality_rating,
        "occupancy_rate": h.occupied_beds / h.total_beds if h.total_beds else 0,
        "is_operational": h.is_operational,
    } for h in result.scalars().all()]


@router.get("/records")
async def recent_records(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MedicalRecord).order_by(MedicalRecord.sim_timestamp.desc()).limit(limit)
    )
    return [{
        "id": str(r.id),
        "citizen_id": str(r.citizen_id),
        "condition": r.condition,
        "condition_type": r.condition_type,
        "severity": r.severity,
        "is_hospitalized": r.is_hospitalized,
        "is_resolved": r.is_resolved,
        "treatment_cost": r.treatment_cost,
        "ticks_remaining": r.ticks_remaining,
        "diagnosis": r.diagnosis,
    } for r in result.scalars().all()]

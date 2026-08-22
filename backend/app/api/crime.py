"""Phase 5 API: Crime & Public Safety endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.crime.crime_engine import CrimeEngine
from backend.app.models.crime import CrimeRecord, PoliceUnit

router = APIRouter(prefix="/api/crime", tags=["crime"])


@router.get("/stats")
async def crime_stats(db: AsyncSession = Depends(get_db)):
    engine = CrimeEngine(db)
    return await engine.get_stats()


@router.get("/recent")
async def recent_crimes(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CrimeRecord).order_by(CrimeRecord.sim_timestamp.desc()).limit(limit)
    )
    return [{
        "id": str(c.id),
        "crime_type": c.crime_type,
        "severity": c.severity,
        "description": c.description,
        "economic_damage": c.economic_damage,
        "is_solved": c.is_solved,
        "response_time_ticks": c.response_time_ticks,
        "sim_timestamp": str(c.sim_timestamp),
    } for c in result.scalars().all()]


@router.get("/police")
async def police_units(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PoliceUnit))
    return [{
        "id": str(u.id),
        "name": u.name,
        "officers": u.officers,
        "effectiveness": u.effectiveness,
        "active_cases": u.active_cases,
        "cases_solved": u.cases_solved,
        "is_active": u.is_active,
    } for u in result.scalars().all()]

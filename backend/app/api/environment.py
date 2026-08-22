"""Phase 6 API: Environment & Sustainability endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.environment import EnvironmentState, GreenInitiative

router = APIRouter(prefix="/api/environment", tags=["environment"])


@router.get("/stats")
async def environment_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EnvironmentState).where(EnvironmentState.is_current.is_(True)).limit(1)
    )
    state = result.scalar_one_or_none()
    if not state:
        return {"status": "no_data"}

    active_init = await db.execute(
        select(sqlfunc.count()).select_from(GreenInitiative).where(GreenInitiative.is_active.is_(True))
    )
    completed_init = await db.execute(
        select(sqlfunc.count()).select_from(GreenInitiative).where(GreenInitiative.is_completed.is_(True))
    )

    return {
        "air_quality_index": state.air_quality_index,
        "water_quality": state.water_quality,
        "noise_level_db": round(state.noise_level_db, 1),
        "green_coverage_pct": round(state.green_coverage_pct, 3),
        "carbon_emissions_tons": round(state.carbon_emissions_tons, 1),
        "recycling_rate": round(state.recycling_rate, 3),
        "renewable_energy_pct": round(state.renewable_energy_pct, 3),
        "waste_tons": round(state.waste_tons, 1),
        "active_initiatives": active_init.scalar() or 0,
        "completed_initiatives": completed_init.scalar() or 0,
    }


@router.get("/initiatives")
async def list_initiatives(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(GreenInitiative).order_by(GreenInitiative.is_active.desc()).limit(limit)
    )
    return [{
        "id": str(i.id),
        "name": i.name,
        "type": i.initiative_type,
        "cost": i.cost,
        "progress": round(i.progress, 3),
        "impact_carbon": i.impact_carbon,
        "impact_air_quality": i.impact_air_quality,
        "is_active": i.is_active,
        "is_completed": i.is_completed,
    } for i in result.scalars().all()]

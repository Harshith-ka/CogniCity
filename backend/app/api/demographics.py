"""Phase 6 API: Demographics & Population endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.demographics import LifeEvent, PopulationSnapshot

router = APIRouter(prefix="/api/demographics", tags=["demographics"])


@router.get("/stats")
async def demographics_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PopulationSnapshot).order_by(PopulationSnapshot.tick.desc()).limit(1)
    )
    snapshot = result.scalar_one_or_none()
    if not snapshot:
        return {"status": "no_data"}

    total_events = await db.execute(select(sqlfunc.count()).select_from(LifeEvent))

    return {
        "total_population": snapshot.total_population,
        "avg_age": snapshot.avg_age,
        "dependency_ratio": snapshot.dependency_ratio,
        "growth_rate": snapshot.growth_rate,
        "births": snapshot.births,
        "deaths": snapshot.deaths,
        "immigrants": snapshot.immigrants,
        "emigrants": snapshot.emigrants,
        "total_life_events": total_events.scalar() or 0,
    }


@router.get("/events")
async def recent_events(limit: int = 30, event_type: str | None = None, db: AsyncSession = Depends(get_db)):
    query = select(LifeEvent).order_by(LifeEvent.sim_timestamp.desc())
    if event_type:
        query = query.where(LifeEvent.event_type == event_type)
    result = await db.execute(query.limit(limit))
    return [{
        "id": str(e.id),
        "citizen_id": str(e.citizen_id),
        "type": e.event_type,
        "description": e.description,
        "related_citizen_id": str(e.related_citizen_id) if e.related_citizen_id else None,
        "timestamp": str(e.sim_timestamp),
    } for e in result.scalars().all()]


@router.get("/snapshots")
async def population_snapshots(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PopulationSnapshot).order_by(PopulationSnapshot.tick.desc()).limit(limit)
    )
    return [{
        "tick": s.tick,
        "total_population": s.total_population,
        "births": s.births,
        "deaths": s.deaths,
        "immigrants": s.immigrants,
        "emigrants": s.emigrants,
        "avg_age": s.avg_age,
        "dependency_ratio": s.dependency_ratio,
        "growth_rate": s.growth_rate,
    } for s in result.scalars().all()]

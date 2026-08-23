"""Phase 6 API: Demographics & Population endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.citizen import Citizen
from backend.app.models.demographics import LifeEvent, PopulationSnapshot

router = APIRouter(prefix="/api/demographics", tags=["demographics"])


@router.get("/live-stats")
async def live_population_stats(db: AsyncSession = Depends(get_db)):
    """Backs the mobile Population Explorer's banner — replaces what used to be
    hardcoded literals (avg age, income, "BMI") with a direct aggregate over the live
    citizens table. Unlike /stats below, this needs no PopulationSnapshot job to have
    run first, so it's never "no_data" as long as the city has been seeded.

    There's no BMI concept anywhere in the citizen model — it was never simulated, so
    reporting it would just be inventing a number. avg_health (the same 0-1 field
    every other health metric in this app is built on) is the honest replacement.
    """
    result = await db.execute(
        select(
            sqlfunc.count(Citizen.id),
            sqlfunc.avg(Citizen.age),
            sqlfunc.avg(Citizen.salary),
            sqlfunc.avg(Citizen.health),
        ).where(Citizen.is_alive == True)  # noqa: E712
    )
    count, avg_age, avg_salary, avg_health = result.one()
    if not count:
        return {"status": "no_data"}

    median_salary_result = await db.execute(
        select(Citizen.salary).where(Citizen.is_alive == True).order_by(Citizen.salary)  # noqa: E712
    )
    salaries = [row[0] for row in median_salary_result.all()]
    median_income = salaries[len(salaries) // 2] if salaries else 0.0

    return {
        "population": count,
        "avg_age": round(float(avg_age), 1),
        "avg_income": round(float(avg_salary), 2),
        "median_income": round(float(median_income), 2),
        "avg_health_pct": round(float(avg_health) * 100, 1),
    }


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

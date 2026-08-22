"""API routes for citizen management."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.app.core.database import get_db
from backend.app.models.citizen import Citizen
from backend.app.models.city import Location
from backend.app.schemas.citizen import CitizenResponse, CitizenSummary, CitizenUpdate

router = APIRouter(prefix="/citizens", tags=["citizens"])


@router.get("/", response_model=list[CitizenSummary])
async def list_citizens(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=2000),
    occupation: str | None = None,
    alive_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    query = select(Citizen).options(
        joinedload(Citizen.current_location).joinedload(Location.district),
        joinedload(Citizen.home_location).joinedload(Location.district),
    )
    if alive_only:
        query = query.where(Citizen.is_alive == True)  # noqa: E712
    if occupation:
        query = query.where(Citizen.occupation == occupation)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    citizens = result.unique().scalars().all()

    summaries = []
    for c in citizens:
        loc = c.current_location or c.home_location
        summaries.append(
            CitizenSummary(
                id=c.id,
                name=c.name,
                age=c.age,
                gender=c.gender,
                occupation=c.occupation,
                happiness=c.happiness,
                stress=c.stress,
                health=c.health,
                energy=c.energy,
                balance=c.balance,
                personality_traits=c.personality_traits or {},
                current_activity=c.current_activity,
                x=loc.x if loc else None,
                y=loc.y if loc else None,
                district_name=loc.district.name if loc and loc.district else None,
            )
        )
    return summaries


@router.get("/{citizen_id}", response_model=CitizenResponse)
async def get_citizen(citizen_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Citizen).where(Citizen.id == citizen_id))
    citizen = result.scalar_one_or_none()
    if not citizen:
        raise HTTPException(status_code=404, detail="Citizen not found")
    return citizen


@router.patch("/{citizen_id}", response_model=CitizenResponse)
async def update_citizen(
    citizen_id: uuid.UUID,
    update: CitizenUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Citizen).where(Citizen.id == citizen_id))
    citizen = result.scalar_one_or_none()
    if not citizen:
        raise HTTPException(status_code=404, detail="Citizen not found")

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(citizen, field, value)

    await db.flush()
    return citizen


@router.get("/{citizen_id}/memories")
async def get_citizen_memories(
    citizen_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    from backend.app.memory.memory_engine import MemoryEngine

    engine = MemoryEngine(db)
    memories = await engine.recall_recent(citizen_id, limit=limit)
    return [
        {
            "id": str(m.id),
            "type": m.memory_type.value,
            "content": m.content,
            "importance": m.importance,
            "emotional_valence": m.emotional_valence,
            "sim_timestamp": m.sim_timestamp.isoformat(),
        }
        for m in memories
    ]


@router.get("/stats/summary")
async def citizen_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Citizen).where(Citizen.is_alive == True)  # noqa: E712
    )
    citizens = list(result.scalars().all())

    if not citizens:
        return {"population": 0}

    return {
        "population": len(citizens),
        "avg_age": sum(c.age for c in citizens) / len(citizens),
        "avg_happiness": sum(c.happiness for c in citizens) / len(citizens),
        "avg_health": sum(c.health for c in citizens) / len(citizens),
        "avg_stress": sum(c.stress for c in citizens) / len(citizens),
        "avg_balance": sum(c.balance for c in citizens) / len(citizens),
        "employed": sum(1 for c in citizens if c.occupation != "unemployed"),
        "unemployed": sum(1 for c in citizens if c.occupation == "unemployed"),
    }


class GrowCityRequest(BaseModel):
    target_population: int = 1000


@router.post("/grow")
async def grow_population(
    req: GrowCityRequest,
    db: AsyncSession = Depends(get_db),
):
    """Add more citizens on top of the existing population — never touches or removes
    anyone already in the city. Adds enough new residential locations/businesses to
    house and employ the newcomers, then seeds relationships among the new arrivals."""
    from backend.app.engine.city_generator import grow_city
    from backend.app.communication.relationship_engine import RelationshipEngine

    current = await db.scalar(select(sqlfunc.count(Citizen.id)).where(Citizen.is_alive == True))  # noqa: E712
    to_add = req.target_population - (current or 0)
    if to_add <= 0:
        return {"status": "no_change", "current_population": current, "added": 0}

    result = await grow_city(db, additional_population=to_add)
    new_citizens = result.pop("new_citizens")

    rel_engine = RelationshipEngine(db)
    relationships_created = await rel_engine.seed_relationships(new_citizens)
    await db.commit()

    return {
        "status": "grown",
        "previous_population": current,
        "added": len(new_citizens),
        "new_population": (current or 0) + len(new_citizens),
        "relationships_created": relationships_created,
        **result,
    }
